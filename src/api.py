import json
import requests

from .my_secrets import PARTNER_CLIENT_ID, PARTNER_ID, PARTNER_SECRET

from flask import Blueprint, request, jsonify

bp = Blueprint("api", __name__, url_prefix="/api")


def request_access_token(client_id, secret):
    endpoint = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    response = requests.post(
        endpoint,
        headers={"Content-Type": "application/json", "Accept-Language": "en_US"},
        data={"grant_type": "client_credentials"},
        auth=(client_id, secret),
    )
    response_dict = response.json()
    return response_dict["access_token"]


def build_headers(client_id=PARTNER_CLIENT_ID, secret=PARTNER_SECRET):
    access_token = request_access_token(client_id, secret)
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }


def generate_sign_up_link(tracking_id, return_url="paypal.com"):
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

    response = requests.post(
        "https://api-m.sandbox.paypal.com/v2/customer/partner-referrals",
        headers=build_headers(),
        data=json.dumps(data),
    )
    response_dict = response.json()

    for link in response_dict["links"]:
        if link["rel"] == "action_url":
            return link["href"]

    # If we're here, no `action_url` was found!
    raise Exception("No action url found!")


def get_merchant_id(tracking_id, partner_id=PARTNER_ID):
    endpoint = f"https://api-m.sandbox.paypal.com/v1/customer/partners/{partner_id}/merchant-integrations?tracking_id={tracking_id}"
    response = requests.get(endpoint, headers=build_headers())

    response_dict = response.json()
    return response_dict["merchant_id"]


def get_status(merchant_id, partner_id=PARTNER_ID):
    endpoint = f"https://api-m.sandbox.paypal.com/v1/customer/partners/{partner_id}/merchant-integrations/{merchant_id}"

    response = requests.get(endpoint, headers=build_headers())

    response_dict = response.json()
    return response_dict


@bp.route("/create-order", methods=("POST",))
def create_order():
    endpoint = "https://api-m.sandbox.paypal.com/v2/checkout/orders"

    headers = build_headers()
    headers["PayPal-Partner-Attribution-Id"] = request.json["bn_code"]

    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "payee": {"merchant_id": request.json["payee_merchant_id"]},
                "amount": {
                    "currency_code": "USD",
                    "value": request.json["price"],
                },
            }
        ],
    }

    response = requests.post(endpoint, headers=headers, data=json.dumps(data))
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/capture-order", methods=("POST",))
def capture_order():
    endpoint = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{request.json['orderId']}/capture"

    headers = build_headers()

    response = requests.post(endpoint, headers=headers)
    response_dict = response.json()
    return jsonify(response_dict)


def get_order_details(order_id):
    endpoint = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}"

    headers = build_headers()

    response = requests.get(endpoint, headers=headers)
    response_dict = response.json()
    return response_dict
