import csv
import base64
import json
import requests
import paramiko
import secrets

from datetime import datetime, timedelta, timezone
from flask import Blueprint, current_app, request, jsonify
from urllib.parse import urlencode

bp = Blueprint("api", __name__, url_prefix="/api")

REPORTS_DIR = "/ppreports/outgoing"
CUSTOMER_ID = "customer_1236"


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

    try:
        kwargs_str = json.dumps(kwargs, indent=2)
    except TypeError:
        kwargs_str = str(kwargs)
    
    current_app.logger.debug(f"\nSending {method} request to {endpoint}:\n{kwargs_str}")

    response = methods_dict[method](endpoint, **kwargs)
    response_str = json.dumps(response.json(), indent=2)
    if not response.ok:
        current_app.logger.error(f"Error: {response_str}\n\n")
    else:
        current_app.logger.debug(f"Response: {response_str}\n\n")

    return response


def request_access_token(client_id, secret):
    """Call the /v1/oauth2/token API to request an access token.

    Docs: https://developer.paypal.com/docs/api/reference/get-an-access-token/
    """
    endpoint = build_endpoint("/v1/oauth2/token")
    headers = {"Content-Type": "application/json", "Accept-Language": "en_US"}

    data = {"grant_type": "client_credentials", "ignoreCache": True}

    response = requests.post(endpoint, headers=headers, data=data, auth=(client_id, secret))
    response_dict = response.json()

    try:
        return response_dict["access_token"]
    except KeyError as exc:
        current_app.logger.error(f"Encountered a KeyError: {exc}")
        current_app.logger.error(
            f"response_dict = {json.dumps(response_dict, indent=2)}"
        )
        raise exc


def build_headers(client_id=None, secret=None, include_bn_code=False):
    """Build commonly used headers using a new PayPal access token."""
    if client_id is None:
        client_id = current_app.config["PARTNER_CLIENT_ID"]
    if secret is None:
        secret = current_app.config["PARTNER_SECRET"] 
    
    access_token = request_access_token(client_id, secret)
    headers = {
        "Accept": "application/json", 
        "Accept-Language": "en_US",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    if include_bn_code:
        headers["PayPal-Partner-Attribution-Id"] = current_app.config["PARTNER_BN_CODE"]
    
    return headers


def build_auth_assertion(client_id=None, merchant_id=None):
    """Build and return the PayPal Auth Assertion.
    Docs: https://developer.paypal.com/docs/api/reference/api-requests/#paypal-auth-assertion
    """
    if client_id is None:
        client_id = current_app.config["PARTNER_CLIENT_ID"]
    if merchant_id is None:
        merchant_id = current_app.config["MERCHANT_ID"]

    header = {"alg": "none"}
    header_b64 = base64.b64encode(json.dumps(header).encode("ascii"))

    payload = {"iss": client_id, "payer_id": merchant_id}
    payload_b64 = base64.b64encode(json.dumps(payload).encode("ascii"))

    signature = b""
    return b".".join([header_b64, payload_b64, signature])


def generate_onboarding_urls(tracking_id, version="v2", return_url="paypal.com"):
    if version == "v1":
        response = create_partner_referral_v1(tracking_id, return_url=return_url)
    else:
        response = create_partner_referral_v2(tracking_id, return_url=return_url)

    onboarding_url = None
    referral_url = None
    for link in response["links"]:
        match link["rel"]:
            case "action_url":
                onboarding_url = link["href"]
            case "self":
                referral_url = link["href"]
            case other:
                raise Exception(f"Unknown onboarding URL relation: {other}")

    if onboarding_url is None or referral_url is None:
        raise Exception("Not all onboarding URLs found!")
    
    return onboarding_url, referral_url
    

def create_partner_referral_v1(tracking_id, return_url):
    """Call the /v1/customer/partner-referrals API to generate a sign-up link.

    Docs: https://developer.paypal.com/docs/api/partner-referrals/v1/#partner-referrals_create
    """
    endpoint = build_endpoint("/v1/customer/partner-referrals")
    headers = build_headers()

    data = {
        "customer_data": {
            "customer_type": "MERCHANT",
            "preferred_language_code": "en_US",
            "primary_currency_code": "USD",
            "partner_specific_identifiers": [
                {
                    "type": "TRACKING_ID",
                    "value": tracking_id
                }
            ]
        },
        "requested_capabilities": [
            {
                "capability": "API_INTEGRATION",
                "api_integration_preference": {
                    "partner_id": current_app.config["PARTNER_ID"],
                    "rest_api_integration": {
                        "integration_method": "PAYPAL",
                        "integration_type": "THIRD_PARTY"
                    },
                    "rest_third_party_details": {
                        "partner_client_id": current_app.config["PARTNER_CLIENT_ID"],
                        "feature_list": [
                            "PAYMENT",
                            "REFUND",
                            "READ_SELLER_DISPUTE"
                        ]
                    }
                }
            }
        ],
        "web_experience_preference": {
            "partner_logo_url": "https://www.paypalobjects.com/digitalassets/c/website/marketing/na/us/logo-center/Badge_1.png",
            "return_url": return_url,
            "action_renewal_url": "www.url.com"
        },
        "collected_consents": [
            {
                "type": "SHARE_DATA_CONSENT",
                "granted": True
            }
        ],
        "products": [
            "EXPRESS_CHECKOUT"
        ]
    }

    response = log_and_request("POST", endpoint, headers=headers, data=json.dumps(data))
    return response.json()


def create_partner_referral_v2(tracking_id, return_url):
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
                                "VAULT"
                            ]
                        },
                    }
                },
            }
        ],
        "products": ["PPCP"],
        "legal_consents": [
            {
                "type": "SHARE_DATA_CONSENT", 
                "granted": True
            }
        ],
        "partner_config_override": {"return_url": return_url},
    }
    data_str = json.dumps(data)

    response = log_and_request("POST", endpoint, headers=headers, data=data_str)
    response_dict = response.json()
    return response_dict




def get_merchant_id(tracking_id, partner_id=None):
    """Call the /v1/customer/partners API to get a merchant's merchant_id.

    Docs: https://developer.paypal.com/docs/platforms/seller-onboarding/before-payment/#5-track-seller-onboarding-status
    """
    if partner_id is None:
        partner_id = current_app.config["PARTNER_ID"]

    endpoint = build_endpoint(
        f"/v1/customer/partners/{partner_id}/merchant-integrations?tracking_id={tracking_id}"
    )
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict["merchant_id"]


def get_onboarding_status(merchant_id, partner_id=None):
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


def get_partner_referral_id(referral_url):
    return referral_url.split('/')[-1]


def get_referral_status(partner_referral_id):
    """Call the /v2/customer/partner-referrals API to get the status of a referral.

    Docs: https://developer.paypal.com/api/partner-referrals/v2/#partner-referrals_read
    """
    endpoint = build_endpoint(
        f"/v2/customer/partner-referrals/{partner_referral_id}"
    )
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict


@bp.route("/create-order", methods=("POST",))
def create_order(include_platform_fees = True):
    """Call the /v2/checkout/orders API to create an order.

    Requires `price` and `payee_id` fields in the request body.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")
    headers = build_headers(include_bn_code=True)

    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "custom_id": "Up to 127 characters can go here!",
                "payee": {"merchant_id": request.json["payee_id"]},
                "amount": {
                    "currency_code": "USD",
                    "value": request.json["price"],
                },
                "soft_descriptor": "1234567890111213141516",
            }
        ],
    }

    if include_platform_fees:
        data['purchase_units'][0]["payment_instruction"] = {
            "disbursement_mode": "INSTANT",
            'platform_fees': [
                {
                    "amount": {
                        "currency_code": "USD", 
                        "value": "1.00"
                    }
                }
            ]
        }

    data_str = json.dumps(data)

    response = log_and_request("POST", endpoint, headers=headers, data=data_str)
    response_dict = response.json()

    current_app.logger.debug(f"Created an order:\n{json.dumps(response_dict,indent=2)}")
    return jsonify(response_dict)


@bp.route("/create-order-vault", methods=("POST",))
def create_order_vault():
    """Call the /v2/checkout/orders API to create an order.

    Requires `price` and `payee_merchant_id` fields in the request body.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")

    headers = build_headers()
    headers["PayPal-Partner-Attribution-Id"] = current_app.config["PARTNER_BN_CODE"]
    headers["PayPal-Request-Id"] = secrets.token_hex(10)

    data = {
        "intent": "CAPTURE",
        "payment_source": {
            "paypal": {
                "attributes": {
                    "customer": {"id": CUSTOMER_ID},
                    "vault": {
                        "confirm_payment_token": "ON_ORDER_COMPLETION",
                        "usage_type": "PLATFORM", # For Channel-Initiated Billing (CIB) Billing Agreement
                        # "usage_type": "MERCHANT", # For Merchant-Initiated Billing (MIB) Billing Agreement
                        "customer_type": "CONSUMER"
                    }
                }
            }
        },
        "purchase_units": [
            {
                "custom_id": "Up to 127 characters can go here!",
                "payee": {"merchant_id": request.json["payee_id"]},
                "payment_instruction": {"disbursement_mode": "INSTANT"},
                "amount": {
                    "currency_code": "USD",
                    "value": request.json["price"],
                },
            }
        ],
        "application_context": {
            "return_url": "http://localhost:5000/",
            "cancel_url": "http://localhost:5000/",
        },
    }
    data_str = json.dumps(data)

    response = log_and_request("POST", endpoint, headers=headers, data=data_str)
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/create-order-auth", methods=("POST",))
def create_order_auth():
    """Call the /v2/checkout/orders API to create an order with intent=AUTHORIZE.

    Requires `price` and `payee_id` fields in the request body.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")
    headers = build_headers(include_bn_code = True)

    data = {
        "intent": "AUTHORIZE",
        "purchase_units": [
            {
                "custom_id": "Up to 127 characters can go here!",
                "payee": {"merchant_id": request.json["payee_id"]},
                "amount": {
                    "currency_code": "USD",
                    "value": request.json["price"],
                },
            }
        ],
    }
    data_str = json.dumps(data)

    response = log_and_request("POST", endpoint, headers=headers, data=data_str)
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/auth-capture/<order_id>", methods=("POST",))
def authorize_and_capture_order(order_id):
    """Authorize and then capture the order."""
    response_dict = authorize_order(order_id)
    auth_id = response_dict['purchase_units'][0]['payments']['authorizations'][0]['id']
    return capture_authorization(auth_id)


def authorize_order(order_id):
    """Authorize the order using the /v2/checkout/orders API.
    
    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_authorize
    """

    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}/authorize")
    headers = build_headers()

    response = log_and_request("POST", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict


def capture_authorization(auth_id, partner_fees = True):
    """Capture the authorization with the given `auth_id` using the /v2/payments/ API.

    Docs: https://developer.paypal.com/docs/api/payments/v2/#authorizations_capture
    """
    endpoint = build_endpoint(f"/v2/payments/authorizations/{auth_id}/capture")
    headers = build_headers()

    if partner_fees:
        data = {
            "payment_instruction": {
                "disbursement_mode": "INSTANT",
                "platform_fees": [
                    {
                        "amount": {
                            "currency_code": "USD", 
                            "value": "1.00"
                        }
                    }
                ]
            }
        }
    else:
        data = {}

    data_str = json.dumps(data)

    response = log_and_request("POST", endpoint, headers=headers, data=data_str)
    response_dict = response.json()
    return jsonify(response_dict)

@bp.route("/capture-order/<order_id>", methods=("POST",))
def capture_order(order_id):
    """Call the /v2/checkout/orders API to capture an order.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}/capture")
    headers = build_headers()

    response = log_and_request("POST", endpoint, headers=headers)
    response_dict = response.json()

    return jsonify(response_dict)


@bp.route("/capture-order-vault", methods=("POST",))
def capture_order_vault():
    """Call the /v2/checkout/orders API to capture an order.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{request.json['orderId']}/capture")
    headers = build_headers()

    response = log_and_request("POST", endpoint, headers=headers)
    response_dict = response.json()

    return jsonify(response_dict)


@bp.route("/capture-order-vault", methods=("POST",))
def capture_order_vault():
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

    verification_str = json.dumps(verification_dict)

    response = log_and_request("POST", endpoint, headers=headers, data=verification_str)
    response_dict = response.json()
    return response_dict


@bp.route("/gen-client-token")
def generate_client_token(customer_id = None):
    if customer_id is None:
        customer_id = CUSTOMER_ID
    endpoint = build_endpoint("/v1/identity/generate-token")
    headers = build_headers()    

    data = {"customer_id": customer_id}
    data_str = json.dumps(data)

    response = requests.post(endpoint, headers=headers, data=data_str)
    response_dict = response.json()
    return response_dict["client_token"]


def build_auth_assertion(client_id=None, merchant_id=None):
    """Build and return the PayPal Auth Assertion.

    Docs: https://developer.paypal.com/docs/api/reference/api-requests/#paypal-auth-assertion
    """
    if client_id is None:
        client_id = current_app.config["PARTNER_CLIENT_ID"]
    if merchant_id is None:
        merchant_id = current_app.config["MERCHANT_ID"]

    header = {"alg": "none"}
    header_b64 = base64.b64encode(json.dumps(header).encode("ascii"))

    payload = {"iss": client_id, "payer_id": merchant_id}
    payload_b64 = base64.b64encode(json.dumps(payload).encode("ascii"))

    signature = b""
    return b".".join([header_b64, payload_b64, signature])


def list_payment_tokens(customer_id=None):
    if customer_id is None:
        customer_id = CUSTOMER_ID

    endpoint = build_endpoint(f"/v2/vault/payment-tokens?customer_id={customer_id}")
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    return response
    

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
