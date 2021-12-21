import json
import requests

from .my_secrets import PARTNER_CLIENT_ID, PARTNER_ID, PARTNER_SECRET

from flask import Blueprint, request, jsonify

bp = Blueprint("api", __name__, url_prefix="/api")


ENVIRONMENT = "sandbox"
if ENVIRONMENT == "live":
    ENDPOINT_PREFIX = "https://api-m.paypal.com"
else:
    ENDPOINT_PREFIX = "https://api-m.sandbox.paypal.com"


def request_access_token(client_id, secret):
    """Call the /v1/oauth2/token API to request an access token.

    Docs: https://developer.paypal.com/docs/api/reference/get-an-access-token/
    """
    endpoint = f"{ENDPOINT_PREFIX}/v1/oauth2/token"
    headers = {"Content-Type": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}

    response = requests.post(
        endpoint, headers=headers, data=data, auth=(client_id, secret)
    )
    response_dict = response.json()
    return response_dict["access_token"]


def build_headers(client_id=PARTNER_CLIENT_ID, secret=PARTNER_SECRET):
    """Build commonly used headers using a new PayPal access token."""
    access_token = request_access_token(client_id, secret)
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }


def generate_sign_up_link(tracking_id, return_url="paypal.com"):
    """Call the /v2/customer/partner-referrals API to generate a sign-up link.

    Docs: https://developer.paypal.com/docs/api/partner-referrals/v2/#partner-referrals_create
    """
    endpoint = f"{ENDPOINT_PREFIX}/v2/customer/partner-referrals"
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

    response = requests.post(endpoint, headers=headers, data=json.dumps(data))
    response_dict = response.json()

    for link in response_dict["links"]:
        if link["rel"] == "action_url":
            return link["href"]

    # If we're here, no `action_url` was found!
    raise Exception("No action url found!")


def get_merchant_id(tracking_id, partner_id=PARTNER_ID):
    """Call the /v1/customer/partners API to get a merchant's merchant_id.

    Docs: https://developer.paypal.com/docs/platforms/seller-onboarding/before-payment/#5-track-seller-onboarding-status
    """
    endpoint = f"{ENDPOINT_PREFIX}/v1/customer/partners/{partner_id}/merchant-integrations?tracking_id={tracking_id}"
    headers = build_headers()

    response = requests.get(endpoint, headers=headers)
    response_dict = response.json()
    return response_dict["merchant_id"]


def get_status(merchant_id, partner_id=PARTNER_ID):
    """Call the /v1/customer/partners API to get the status of a merchant's onboarding.

    Docs: https://developer.paypal.com/docs/platforms/seller-onboarding/before-payment/#5-track-seller-onboarding-status
    """
    endpoint = f"{ENDPOINT_PREFIX}/v1/customer/partners/{partner_id}/merchant-integrations/{merchant_id}"
    headers = build_headers()

    response = requests.get(endpoint, headers=headers)
    response_dict = response.json()
    return response_dict


@bp.route("/create-order", methods=("POST",))
def create_order():
    """Call the /v2/checkout/orders API to create an order.

    Requires `bn_code`, `price`, and `payee_merchant_id` fields in the request body.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = f"{ENDPOINT_PREFIX}/v2/checkout/orders"

    headers = build_headers()
    headers["PayPal-Partner-Attribution-Id"] = request.json["bn_code"]

    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "payee": {"merchant_id": request.json["payee_merchant_id"]},
                "payment_instruction": {"disbursement_mode": "INSTANT"},
                "amount": {
                    "currency_code": "USD",
                    "value": request.json["price"],
                },
                "shipping": {
                    "options": [
                        {
                            "id": "SHIP_123",
                            "label": "Free Shipping",
                            "type": "SHIPPING",
                            "selected": True,
                            "amount": {"value": "3.00", "currency_code": "USD"},
                        },
                        {
                            "id": "SHIP_456",
                            "label": "Pick up in Store",
                            "type": "SHIPPING",
                            "selected": False,
                            "amount": {"value": "0.00", "currency_code": "USD"},
                        },
                    ]
                },
            }
        ],
    }

    response = requests.post(endpoint, headers=headers, data=json.dumps(data))
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/capture-order", methods=("POST",))
def capture_order():
    """Call the /v2/checkout/orders API to capture an order.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
    """
    endpoint = f"{ENDPOINT_PREFIX}/v2/checkout/orders/{request.json['orderId']}/capture"
    headers = build_headers()

    response = requests.post(endpoint, headers=headers)
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/update-shipping", methods=("POST",))
def update_shipping():
    """Call the /v2/checkout/orders API to update the shipping on an order.

    Docs: https://developer.paypal.com/api/orders/v2/#orders_patch
    """
    print(f"It's time to update shipping! Received data:")
    print(json.dumps(request.json, indent=2))

    my_json = request.json
    endpoint = f"{ENDPOINT_PREFIX}/v2/checkout/orders/{my_json['order_id']}"
    headers = build_headers()
    data = {
        "op": "replace",
        "path": "/purchase_units/@reference_id=='default'/shipping/options",
        "value": [
            {
                "id": "SHIP_420",
                "label": "Nice, cheap shipping",
                "type": "SHIPPING",
                "selected": True,
                "amount": {"value": "0.99", "currency_code": "USD"},
            },
            {
                "id": "SHIP_421",
                "label": "Inconvenient shipping",
                "type": "SHIPPING",
                "selected": False,
                "amount": {"value": "0.01", "currency_code": "USD"},
            },
        ],
    }

    response = requests.patch(endpoint, headers=headers, data=json.dumps(data))

    response_dict = response.json()
    print(f"Shipping update response: \n{json.dumps(response_dict, indent=2)}")
    return jsonify(response_dict)
    # return "", 204


def get_order_details(order_id):
    """Call the /v2/checkout/orders API to get order details.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_get
    """
    endpoint = f"{ENDPOINT_PREFIX}/v2/checkout/orders/{order_id}"
    headers = build_headers()

    response = requests.get(endpoint, headers=headers)
    response_dict = response.json()
    return response_dict
