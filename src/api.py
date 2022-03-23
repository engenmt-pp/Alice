import json
import requests

from flask import Blueprint, current_app, request, jsonify

bp = Blueprint("api", __name__, url_prefix="/api")


def build_endpoint(route):
    """Build the appropriate API endpoint given the suffix/route."""
    endpoint_prefix = current_app.config["ENDPOINT_PREFIX"]
    return f"{endpoint_prefix}{route}"


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

    response = methods_dict[method](endpoint, **kwargs)
    if not response.ok:
        current_app.logger.error(f"Error: {response.text}")

    return response


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
    return response_dict["access_token"]


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


def generate_onboarding_urls(tracking_id, return_url="paypal.com"):
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
    data_str = json.dumps(data)

    response = log_and_request("POST", endpoint, headers=headers, data=data_str)
    response_dict = response.json()

    onboarding_url = None
    referral_url = None
    for link in response_dict["links"]:
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
                "custom_id": "Up to 127 characters can go here!",
                "payee": {"merchant_id": request.json["payee_id"]},
                "payment_instruction": {"disbursement_mode": "INSTANT"},
                "amount": {
                    "currency_code": "USD",
                    "value": request.json["price"],
                },
                "soft_descriptor": "1234567890111213141516",
            }
        ],
    }
    data_str = json.dumps(data)

    response = log_and_request("POST", endpoint, headers=headers, data=data_str)
    response_dict = response.json()

    current_app.logger.debug(f"Created an order:\n{json.dumps(response_dict,indent=2)}")
    return jsonify(response_dict)


@bp.route("/create-order-vault", methods=("POST",))
def create_order_vault():
    """Call the /v2/checkout/orders API to create an order.

    Requires `bn_code`, `price`, and `payee_merchant_id` fields in the request body.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")

    headers = build_headers()
    headers["PayPal-Partner-Attribution-Id"] = request.json["bn_code"]

    data = {
        "processing_instruction": "NO_INSTRUCTION",
        "intent": "CAPTURE",
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
            "return_url": "https://paypal.com",
        },
    }
    data_str = json.dumps(data)

    response = log_and_request("POST", endpoint, headers=headers, data=data_str)
    response_dict = response.json()

    current_app.logger.debug(
        f"Created an order for vaulting:\n{json.dumps(response_dict,indent=2)}"
    )
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

    current_app.logger.debug(
        f"Captured an order:\n{json.dumps(response_dict,indent=2)}"
    )
    return jsonify(response_dict)


@bp.route("/capture-order-vault", methods=("POST",))
def capture_order_vault():
    """Call the /v2/checkout/orders API to capture an order.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{request.json['orderId']}/capture")
    headers = build_headers()

    data = {
        "payment_source": {
            "paypal": {
                "attributes": {
                    "customer": {"id": "customer_1234"},
                    "vault": {
                        "confirm_payment_token": "ON_ORDER_COMPLETION",
                        "usage_type": "MERCHANT",
                        "customer_type": "CONSUMER",
                    },
                }
            }
        },
        "application_context": {
            "cancel_url": "https://paypal.com",
            "return_url": "https://paypal.com",
        },
    }
    data_str = json.dumps(data)

    response = log_and_request("POST", endpoint, headers=headers, data=data_str)
    response_dict = response.json()

    current_app.logger.debug(
        f"Captured an order for vaulting:\n{json.dumps(response_dict,indent=2)}"
    )
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
def generate_client_token():
    headers = build_headers()
    headers |= {"Accept": "application/json", "Accept-Language": "en_US"}

    endpoint = build_endpoint("/v1/identity/generate-token")

    data = {"customer_id": "customer_1234"}
    data_str = json.dumps(data)

    response = log_and_request("POST", endpoint, headers=headers, data=data_str)
    response_dict = response.json()
    return response_dict["client_token"]
