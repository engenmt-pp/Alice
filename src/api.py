import base64
import json
import requests

from datetime import datetime, timedelta, timezone
from flask import Blueprint, current_app, request, jsonify
from urllib.parse import urlencode

bp = Blueprint("api", __name__, url_prefix="/api")


def build_endpoint(route, query=None):
    """Build the appropriate API endpoint given the suffix/route."""
    endpoint_prefix = current_app.config["ENDPOINT_PREFIX"]
    endpoint = f"{endpoint_prefix}{route}"
    if query is None:
        return endpoint

    query_string = urlencode(query)
    return f"{endpoint}?{query_string}"


def log_and_request(method, endpoint, **kwargs):
    """Log the HTTP request, make the request, and return the response."""
    methods_dict = {
        "POST": requests.post,
        "GET": requests.get,
    }
    if method not in methods_dict:
        raise Exception(f"HTTP request method '{method}' not recognized!")

    current_app.logger.debug(
        f"\nSending {method} request to {endpoint}:\n{json.dumps(kwargs, indent=2)}"
    )

    return methods_dict[method](endpoint, **kwargs)


def request_access_token(client_id, secret):
    """Call the /v1/oauth2/token API to request an access token.

    Docs: https://developer.paypal.com/docs/api/reference/get-an-access-token/
    """
    endpoint = build_endpoint("/v1/oauth2/token")
    headers = {"Content-Type": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}

    response = log_and_request(
        "POST", endpoint, headers=headers, data=data, auth=(client_id, secret)
    )
    response_dict = response.json()

    try:
        return response_dict["access_token"]
    except KeyError as exc:
        current_app.logger.error(f"Encountered a KeyError: {exc}")
        current_app.logger.error(
            f"response_dict = {json.dumps(response_dict, indent=2)}"
        )
        raise exc


def build_headers(client_id=None, secret=None):
    """Build commonly used headers using a new PayPal access token."""
    if client_id is None:
        client_id = current_app.config["PARTNER_CLIENT_ID"]
    if secret is None:
        secret = current_app.config["PARTNER_SECRET"]
    access_token = request_access_token(client_id, secret)
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }


def generate_sign_up_link(tracking_id, return_url="paypal.com"):
    """Call the /v2/customer/partner-referrals API to generate a sign-up link.

    Docs: https://developer.paypal.com/docs/api/partner-referrals/v2/#partner-referrals_create
    """
    endpoint = build_endpoint("/v2/customer/partner-referrals")
    headers = build_headers()
    data = {
        "tracking_id": tracking_id,
        "operations": [
            {
                "operation": "API_INTEGRATION",
                "api_integration_preference": {
                    "rest_api_integration": {
                        "integration_method": "PAYPAL",
                        "integration_type": "THIRD_PARTY",
                        "third_party_details": {
                            "features": [
                                "PAYMENT",
                                "REFUND",
                                "PARTNER_FEE",
                                "DELAY_FUNDS_DISBURSEMENT",
                            ]
                        },
                    }
                },
            }
        ],
        "products": ["PPCP"],
        "legal_consents": [{"type": "SHARE_DATA_CONSENT", "granted": True}],
        "partner_config_override": {"return_url": return_url},
    }

    response = log_and_request("POST", endpoint, headers=headers, data=json.dumps(data))
    response_dict = response.json()

    for link in response_dict["links"]:
        if link["rel"] == "action_url":
            return link["href"]

    # If we're here, no `action_url` was found!
    raise Exception("No action url found!")


def get_merchant_id(tracking_id, partner_id=None):
    """Call the /v1/customer/partners API to get a merchant's merchant_id.

    Docs: https://developer.paypal.com/docs/platforms/seller-onboarding/before-payment/#5-track-seller-onboarding-status
    """
    if partner_id is None:
        partner_id = current_app.config["PARTNER_ID"]

    endpoint = endpoint = build_endpoint(
        f"/v1/customer/partners/{partner_id}/merchant-integrations?tracking_id={tracking_id}"
    )
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict["merchant_id"]


def get_status(merchant_id, partner_id=None):
    """Call the /v1/customer/partners API to get the status of a merchant's onboarding.

    Docs: https://developer.paypal.com/docs/platforms/seller-onboarding/before-payment/#5-track-seller-onboarding-status
    """
    if partner_id is None:
        partner_id = current_app.config["PARTNER_ID"]

    endpoint = build_endpoint(
        f"/v1/customer/partners/{partner_id}/merchant-integrations/{merchant_id}"
    )
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict


@bp.route("/create-order", methods=("POST",))
def create_order():
    """Call the /v2/checkout/orders API to create an order.

    Requires `bn_code`, `price`, and `payee_merchant_id` fields in the request body.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")

    headers = build_headers()
    headers["PayPal-Partner-Attribution-Id"] = request.json["bn_code"]

    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "payee": {"merchant_id": request.json["payee_id"]},
                "payment_instruction": {"disbursement_mode": "INSTANT"},
                "amount": {
                    "currency_code": "USD",
                    "value": request.json["price"],
                },
            }
        ],
    }

    response = log_and_request("POST", endpoint, headers=headers, data=json.dumps(data))
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/capture-order", methods=("POST",))
def capture_order():
    """Call the /v2/checkout/orders API to capture an order.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{request.json['orderId']}/capture")
    headers = build_headers()

    response = log_and_request("POST", endpoint, headers=headers)
    response_dict = response.json()
    return jsonify(response_dict)


def get_order_details(order_id):
    """Call the /v2/checkout/orders API to get order details.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_get
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}")
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict


def verify_webhook_signature(verification_dict):
    """Verify the signature of the webhook to ensure it is genuine.

    Docs: https://developer.paypal.com/api/webhooks/v1/#verify-webhook-signature_post
    """
    endpoint = build_endpoint("/v1/notifications/verify-webhook-signature")
    headers = build_headers()

    response = log_and_request(
        "POST", endpoint, headers=headers, data=json.dumps(verification_dict)
    )
    response_dict = response.json()
    return response_dict


def build_auth_assertion(client_id=None, merchant_id=None):
    """Build and return the PayPal Auth Assertion.

    See https://developer.paypal.com/docs/api/reference/api-requests/#paypal-auth-assertion for details.
    """
    if client_id is None:
        client_id = current_app.config["PARTNER_CLIENT_ID"]
    if merchant_id is None:
        client_id = current_app.config["MERCHANT_ID"]

    header = {"alg": "none"}
    header_b64 = base64.b64encode(json.dumps(header).encode("ascii"))

    payload = {"iss": client_id, "payer_id": merchant_id}
    payload_b64 = base64.b64encode(json.dumps(payload).encode("ascii"))

    signature = b""

    return b".".join([header_b64, payload_b64, signature])


def refund_order(capture_id, client_id):
    endpoint = build_endpoint(f"/v2/payments/captures/{capture_id}/refund")

    headers = build_headers()
    headers["PayPal-Auth-Assertion"] = build_auth_assertion()

    data = {"note_to_payer": "Apologies for the inconvenience!"}

    response = requests.post(endpoint, headers=headers, data=json.dumps(data))
    response_dict = response.json()
    return response_dict


def get_transactions():
    """Get the transactions from the preceding four weeks.

    Docs: https://developer.paypal.com/docs/api/transaction-search/v1/
    """
    headers = build_headers()

    end_date = datetime.now(tz=timezone.utc)
    start_date = end_date - timedelta(days=28)

    query = {
        "start_date": start_date.isoformat(timespec="seconds"),
        "end_date": end_date.isoformat(timespec="seconds"),
    }
    endpoint = build_endpoint("/v1/reporting/transactions", query)

    response = requests.get(endpoint, headers=headers)
    response_dict = response.json()
    return response_dict


def build_auth_assertion(client_id, merchant_payer_id):
    """Build and return the PayPal Auth Assertion.

    See https://developer.paypal.com/docs/api/reference/api-requests/#paypal-auth-assertion for details.
    """
    header = {"alg": "none"}
    payload = {"iss": client_id, "payer_id": merchant_payer_id}
    signature = b""
    header_b64 = base64.b64encode(json.dumps(header).encode("ascii"))
    payload_b64 = base64.b64encode(json.dumps(payload).encode("ascii"))
    return b".".join([header_b64, payload_b64, signature])


def refund_order(capture_id):

    endpoint = (
        f"https://api-m.sandbox.paypal.com/v2/payments/captures/{capture_id}/refund"
    )

    client_id = PARTNER_CLIENT_ID  # partner client ID
    merchant_payer_id = merchant_id  # merchant merchant ID
    headers = build_headers()
    headers["PayPal-Auth-Assertion"] = build_auth_assertion(
        client_id, merchant_payer_id
    )

    data = {"note_to_payer": "Apologies for the inconvenience!"}

    response = requests.post(endpoint, headers=headers, data=json.dumps(data))
    response_dict = response.json()
    return response_dict


def get_transactions():
    """Get the transactions from the preceding four weeks.

    Docs: https://developer.paypal.com/docs/api/transaction-search/v1/
    """
    end_date = datetime.now(tz=timezone.utc)
    start_date = end_date - timedelta(days=28)

    headers = build_headers()

    data = {
        "start_date": start_date.isoformat(timespec="seconds"),
        "end_date": end_date.isoformat(timespec="seconds"),
    }
    data_encoded = urlencode(data)

    endpoint_prefix = "https://api-m.sandbox.paypal.com/v1/reporting/transactions"
    endpoint = f"{endpoint_prefix}?{data_encoded}"

    response = requests.get(endpoint, headers=headers)
    response_dict = response.json()
    return response_dict


def refund_order(capture_id):

    endpoint = f"{ENDPOINT_PREFIX}/v2/payments/captures/{capture_id}/refund"

    client_id = PARTNER_CLIENT_ID  # partner client ID
    merchant_payer_id = MERCHANT_ID  # merchant merchant ID
    headers = build_headers()
    headers["PayPal-Auth-Assertion"] = build_auth_assertion(
        client_id, merchant_payer_id
    )

    data = {"note_to_payer": "Apologies for the inconvenience!"}

    response = requests.post(endpoint, headers=headers, data=json.dumps(data))
    response_dict = response.json()
    return response_dict


def get_transactions(as_merchant=False):
    """Get the transactions from the preceding four weeks.

    Docs: https://developer.paypal.com/docs/api/transaction-search/v1/
    """

    if as_merchant:
        # This doesn't work!
        headers = build_headers(client_id=MERCHANT_CLIENT_ID, secret=MERCHANT_SECRET)
    else:
        headers = build_headers(client_id=PARTNER_CLIENT_ID, secret=PARTNER_SECRET)

    # This works, but is unnecessary.
    headers["PayPal-Auth-Assertion"] = build_auth_assertion(
        client_id=PARTNER_CLIENT_ID, merchant_payer_id=MERCHANT_ID
    )

    end_date = datetime.now(tz=timezone.utc)
    start_date = end_date - timedelta(days=28)
    data = {
        "start_date": start_date.isoformat(timespec="seconds"),
        "end_date": end_date.isoformat(timespec="seconds"),
    }
    data_encoded = urlencode(data)

    endpoint = f"{ENDPOINT_PREFIX}/v1/reporting/transactions?{data_encoded}"

    response = requests.get(endpoint, headers=headers)
    response_dict = response.json()
    return response_dict
