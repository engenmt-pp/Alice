from flask import Blueprint, current_app, jsonify, request

from .utils import (
    build_endpoint,
    build_headers,
    log_and_request,
    format_request_and_response,
)

bp = Blueprint("orders_form", __name__, url_prefix="/orders-form")


def default_shipping_option():
    return {
        "id": "shipping-default",
        "label": "A default shipping option",
        "selected": True,
        "amount": {
            "currency_code": "USD",
            "value": "9.99",
        },
    }


def build_purchase_unit(
    partner_id,
    merchant_id,
    price,
    include_shipping_options,
    partner_fee=0,
    reference_id=None,
):

    purchase_unit = {
        "custom_id": "Up to 127 characters can go here!",
        "payee": {"merchant_id": merchant_id},
        "amount": {
            "currency_code": "USD",
            "value": price,
        },
        "soft_descriptor": "1234567890111213141516",
    }

    if reference_id is not None:
        purchase_unit["reference_id"] = reference_id

    if partner_fee > 0:
        purchase_unit["payment_instruction"]["platform_fees"] = [
            {
                "amount": {"currency_code": "USD", "value": partner_fee},
                "payee": {"merchant_id": partner_id},
            }
        ]

    if include_shipping_options:
        shipping_options = [default_shipping_option()]
        purchase_unit["shipping"] = {"options": shipping_options}

    return purchase_unit


def build_application_context(shipping_preference):
    return {
        "return_url": "http://localhost:5000/",
        "cancel_url": "http://localhost:5000/",
        "shipping_preference": shipping_preference,
    }


@bp.route("/create", methods=("POST",))
def create_order_router():
    """Create an order with the /v2/checkout/orders API.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    form_options = request.get_json()

    headers = build_headers(return_formatted=True)
    formatted = {"access-token": headers["formatted"]}
    del headers["formatted"]

    create_response = create_order(headers, form_options)
    formatted["create-order"] = format_request_and_response(create_response)

    order_id = create_response.json()["id"]
    response_dict = {"formatted": formatted, "orderId": order_id}
    return jsonify(response_dict)


def create_order(headers, form_options):
    """Create an order with the /v2/checkout/orders API.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")

    shipping_preference = form_options["shipping-preference"]

    partner_id = form_options["partner-id"]
    merchant_id = form_options["merchant-id"]
    price = form_options["price"]
    include_shipping_options = shipping_preference != "NO_SHIPPING"
    purchase_unit = build_purchase_unit(
        partner_id=partner_id,
        merchant_id=merchant_id,
        price=price,
        include_shipping_options=include_shipping_options,
    )

    intent = form_options["intent"]

    application_context = build_application_context(shipping_preference)

    data = {
        "application_context": application_context,
        "intent": intent,
        "purchase_units": [purchase_unit],
    }

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    return response


@bp.route("/capture/<order_id>", methods=("POST",))
def capture_order_router(order_id):
    """Capture the order with the /v2/checkout/orders API.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
    """
    form_options = request.get_json()
    intent = form_options["intent"]
    if intent == "AUTHORIZE":
        formatted_dict = auth_and_capture_order(order_id, form_options)
    else:
        capture_response = capture_order(order_id)
        formatted_dict = {
            "capture-order": format_request_and_response(capture_response)
        }

    return jsonify({"formatted": formatted_dict})


def auth_and_capture_order(order_id, form_options):
    """Authorize and then capture the order according to the provided form options.

    Return a dictionary of the formatted requests and responses.
    """
    auth_response = authorize_order(order_id)
    formatted_dict = {"authorize-order": format_request_and_response(auth_response)}
    auth_id = auth_response.json["purchase_units"][0]["payments"]["authorizations"][0]

    capture_response = capture_authorization(auth_id, form_options)
    formatted_dict["capture-order"] = format_request_and_response(capture_response)
    return formatted_dict


def authorize_order(order_id):
    """Authorize the order using the /v2/checkout/orders API.

    Returns the response object.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_authorize
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}/authorize")
    headers = build_headers()

    response = log_and_request("POST", endpoint, headers=headers)
    return response


def capture_order(order_id):
    """Capture the order with the /v2/checkout/orders API.

    Returns the response object.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}/capture")
    headers = build_headers()

    response = log_and_request("POST", endpoint, headers=headers)
    return response


def capture_authorization(auth_id, form_options):
    """Capture the authorization with the given `auth_id` using the /v2/payments API.

    Returns the response object.

    Docs: https://developer.paypal.com/docs/api/payments/v2/#authorizations_capture
    """
    endpoint = build_endpoint(f"/v2/payments/authorizations/{auth_id}/capture")
    headers = build_headers()

    partner_fees = float(form_options["partner-fee"])
    if partner_fees > 0:
        data = {
            "payment_instruction": {
                "platform_fees": [
                    {"amount": {"currency_code": "USD", "value": partner_fees}}
                ],
            }
        }
    else:
        data = {}

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    return response
