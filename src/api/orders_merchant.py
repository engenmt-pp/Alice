from flask import Blueprint, current_app, jsonify, request

from .utils import (
    build_endpoint,
    log_and_request,
    random_decimal_string,
)

from .identity import request_access_token

bp = Blueprint("orders_merchant", __name__, url_prefix="/orders-merchant")


def default_purchase_unit(payee_id, price):
    return {
        "payee": {"merchant_id": payee_id},
        "amount": {
            "currency_code": "USD",
            "value": price,
        },
    }


def build_headers_merchant(client_id=None, secret=None):
    """Build commonly used headers using a new PayPal access token."""
    if client_id is None:
        client_id = current_app.config["MERCHANT_CLIENT_ID"]
    if secret is None:
        secret = current_app.config["MERCHANT_SECRET"]

    access_token = request_access_token(client_id, secret)
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    return headers


@bp.route("/create-vault", methods=("POST",))
def create_order_vault():
    """Create an order for vaulting with the /v2/checkout/orders API.

    Notes:
      - Requires `customer_id`, `payee_id`, and `price` fields in the request body.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")
    headers = build_headers_merchant()
    headers["PayPal-Request-Id"] = random_decimal_string(length=10)

    customer_id = request.json["customer_id"]
    payee_id = request.json["payee_id"]
    price = request.json["price"]

    data = {
        "intent": "CAPTURE",
        "payment_source": {
            "paypal": {
                "attributes": {
                    "customer": {"id": customer_id},
                    "vault": {
                        "confirm_payment_token": "ON_ORDER_COMPLETION",
                        "usage_type": "MERCHANT",  # For Merchant-Initiated Billing (MIB) Billing Agreement
                        "customer_type": "CONSUMER",
                    },
                }
            }
        },
        "purchase_units": [default_purchase_unit(payee_id, price)],
        "application_context": {
            "return_url": "http://localhost:5000/",
            "cancel_url": "http://localhost:5000/",
            "permit_multiple_payment_tokens": True,
        },
    }

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/capture/<order_id>", methods=("POST",))
def capture_order(order_id):
    """Capture the order with the /v2/checkout/orders API.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}/capture")
    headers = build_headers_merchant()

    response = log_and_request("POST", endpoint, headers=headers)
    response_dict = response.json()
    return jsonify(response_dict)


def get_order_details(order_id):
    """Get the details of the order with the /v2/checkout/orders API.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_get
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}")
    headers = build_headers_merchant()

    response = log_and_request("GET", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict


def get_payment_tokens(customer_id):
    """Return the payment tokens vaulted with the given `customer_id` with the /v2/vault API.

    Docs: https://developer.paypal.com/limited-release/vault-payment-methods/orders-api
    """
    query = {"customer_id": customer_id}
    endpoint = build_endpoint(f"/v2/vault/payment-tokens", query=query)
    headers = build_headers_merchant()

    response = log_and_request("GET", endpoint, headers=headers)
    return response
