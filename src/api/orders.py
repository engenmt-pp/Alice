import json
from datetime import datetime, timedelta, timezone
from flask import Blueprint, current_app, jsonify, request

from .utils import (
    build_endpoint,
    build_headers,
    log_and_request,
    random_decimal_string,
)


bp = Blueprint("orders", __name__, url_prefix="/orders")


def default_purchase_unit(payee_id, price=3.14, reference_id=None):
    purchase_unit = {
        "custom_id": "Up to 127 characters can go here!",
        "payee": {"merchant_id": payee_id},
        "amount": {
            "currency_code": "USD",
            "value": price,
        },
        "soft_descriptor": "1234567890111213141516",
    }
    if reference_id is not None:
        purchase_unit["reference_id"] = reference_id
    return purchase_unit


@bp.route("/create", methods=("POST",))
def create_order(include_platform_fees=True):
    """Create an order with the /v2/checkout/orders API.

    Notes:
      - Requires `payee_id` and `price` fields in the request body.
      - Request body can contain the flag `include_shipping` to include a default
        shipping option.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")
    headers = build_headers(include_bn_code=True)

    payee_id = request.json["payee_id"]
    price = request.json["price"]
    data = {
        "intent": "CAPTURE",
        "purchase_units": [default_purchase_unit(payee_id, price)],
        "application_context": {
            "return_url": "http://localhost:5000/",
            "cancel_url": "http://localhost:5000/",
            "shipping_preference": "NO_SHIPPING",
        },
    }

    if include_platform_fees:
        data["purchase_units"][0]["payment_instruction"] = {
            "disbursement_mode": "INSTANT",
            "platform_fees": [{"amount": {"currency_code": "USD", "value": "1.00"}}],
        }

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/create-vault", methods=("POST",))
def create_order_vault():
    """Create an order for vaulting with the /v2/checkout/orders API.

    Notes:
      - Requires `customer_id`, `payee_id`, and `price` fields in the request body.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")
    headers = build_headers(include_bn_code=True)
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
                        "customer_type": "CONSUMER",
                        "confirm_payment_token": "ON_ORDER_COMPLETION",
                        "usage_type": "PLATFORM",  # For partner-level vaulting
                        "permit_multiple_payment_tokens": True,
                    },
                }
            }
        },
        "purchase_units": [default_purchase_unit(payee_id, price)],
        "application_context": {
            "return_url": "http://localhost:5000/returnURL",
            "cancel_url": "http://localhost:5000/cancelURL",
        },
    }

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/not-present", methods=("POST",))
def order_not_present():
    """Create and capture an order using a vaulted payment method with the /v2/checkout/orders API.

    Notes:
      - Requires `customer_id`, `payee_id`, and `price` fields in the request body.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")
    headers = build_headers(include_bn_code=True)
    headers["PayPal-Request-Id"] = random_decimal_string(length=10)

    customer_id = request.json["customer_id"]
    payee_id = request.json["payee_id"]
    price = request.json["price"]

    payment_tokens_resp = get_payment_tokens(customer_id).json()
    payment_tokens = payment_tokens_resp["payment_tokens"]
    try:
        token_id = payment_tokens[0]["id"]
    except IndexError as exc:
        current_app.error(
            "No payment tokens found! Payment token response:"
            f"\n{json.dumps(payment_tokens_resp, indent=2)}"
        )
        raise exc

    data = {
        "intent": "CAPTURE",
        "payment_source": {
            "token": {
                "type": "PAYMENT_METHOD_TOKEN",
                "id": token_id,
            },
            "vault": {"usage_type": "PLATFORM", "customer_type": "CONSUMER"},
        },
        "purchase_units": [default_purchase_unit(payee_id, price)],
    }

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/create-auth", methods=("POST",))
def create_order_auth():
    """Create an order for auth-capture with the /v2/checkout/orders API.

    Notes:
      - Requires `price` and `payee_id` fields in the request body.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")
    headers = build_headers(include_bn_code=True)

    payee_id = request.json["payee_id"]
    price = request.json["price"]
    data = {
        "intent": "AUTHORIZE",
        "purchase_units": [default_purchase_unit(payee_id, price)],
        "application_context": {"shipping_preference": "GET_FROM_FILE"},
    }

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/auth-capture/<order_id>", methods=("POST",))
def authorize_and_capture_order(order_id):
    """Authorize and capture the order, returning the capture response."""
    authorization = authorize_order(order_id)
    auth_id = authorization["id"]
    return capture_authorization(auth_id)


@bp.route("/authorize/<order_id>", methods=("POST",))
def authorize_order(order_id):
    """Authorize the order using the /v2/checkout/orders API.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_authorize
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}/authorize")
    headers = build_headers()

    response = log_and_request("POST", endpoint, headers=headers)
    response_dict = response.json()
    authorization = response_dict["purchase_units"][0]["payments"]["authorizations"][0]
    return authorization


@bp.route("/capture-auth/<auth_id>", methods=("POST",))
def capture_authorization(auth_id, include_partner_fees=True):
    """Capture the authorization with the given `auth_id` using the /v2/payments API.

    Docs: https://developer.paypal.com/docs/api/payments/v2/#authorizations_capture
    """
    endpoint = build_endpoint(f"/v2/payments/authorizations/{auth_id}/capture")
    headers = build_headers()

    if include_partner_fees:
        data = {
            "payment_instruction": {
                "disbursement_mode": "INSTANT",
                "platform_fees": [
                    {"amount": {"currency_code": "USD", "value": "1.00"}}
                ],
            }
        }
    else:
        data = {}

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/capture/<order_id>", methods=("POST",))
def capture_order(order_id):
    """Capture the order with the /v2/checkout/orders API.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}/capture")
    headers = build_headers()

    response = log_and_request("POST", endpoint, headers=headers)
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/determine-shipping", methods=("GET",))
def determine_shipping():
    """Determine new shipping options given a customer's shipping address.

    Notes:
      - This method returns a hard-coded determined shipping option.
    """
    return jsonify(
        [
            {
                "id": "shipping-determined",
                "label": "A determined shipping option",
                "selected": True,
                "amount": {
                    "currency_code": "USD",
                    "value": "4.99",
                },
            }
        ]
    )


@bp.route("/update-shipping/<order_id>", methods=("POST",))
def update_shipping(order_id):
    """Update the order's shipping option with the /v2/checkout/orders API.

    Notes:
      - In sandbox, this occaisionally fails to result in updated shipping options despite a 204 response.

    Docs: https://developer.paypal.com/api/orders/v2/#orders_patch
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}")
    headers = build_headers()

    data = [
        {
            "op": "replace",
            "path": "/purchase_units/@reference_id=='default'/shipping/options",
            "value": [
                {
                    "id": "shipping-updated",
                    "label": "An updated shipping option",
                    "selected": True,
                    "amount": {
                        "currency_code": "USD",
                        "value": "9.99",
                    },
                }
            ],
        }
    ]
    response = log_and_request("PATCH", endpoint, headers=headers, data=data)
    if response.status_code == 204:
        return {}

    response_dict = response.json()
    return response_dict


def get_order_details(order_id):
    """Get the details of the order with the /v2/checkout/orders API.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_get
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}")
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict


def refund_order(capture_id):
    """Refund the capture with the /v2/payments API.

    Docs: https://developer.paypal.com/docs/api/payments/v2/#captures_refund
    """
    endpoint = build_endpoint(f"/v2/payments/captures/{capture_id}/refund")
    headers = build_headers(include_auth_assertion=True)

    data = {"note_to_payer": "Apologies for the inconvenience!"}

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    response_dict = response.json()
    return response_dict


def get_payment_tokens(customer_id):
    """Return the payment tokens vaulted with the given `customer_id` with the /v2/vault API.

    Docs: https://developer.paypal.com/limited-release/vault-payment-methods/orders-api
    """
    query = {"customer_id": customer_id}
    endpoint = build_endpoint(f"/v2/vault/payment-tokens", query=query)
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    return response


def get_transactions():
    """Get the transactions from the preceding four weeks with the /v1/reporting API.

    Notes:
      - This requires the "ADVANCED_TRANSACTIONS_SEARCH" option enabled at onboarding.

    Docs: https://developer.paypal.com/docs/api/transaction-search/v1/
    """
    headers = build_headers(include_auth_assertion=True)

    end_date = datetime.now(tz=timezone.utc)
    start_date = end_date - timedelta(days=28)
    query = {
        "start_date": start_date.isoformat(timespec="seconds"),
        "end_date": end_date.isoformat(timespec="seconds"),
    }

    endpoint = build_endpoint(f"/v1/reporting/transactions", query)

    response = log_and_request("GET", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict
