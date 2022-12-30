from flask import Blueprint, current_app, jsonify, request

import json

from .utils import (
    build_endpoint,
    build_headers,
    log_and_request,
    format_request_and_response,
)

bp = Blueprint("orders_form", __name__, url_prefix="/orders-form")


def default_shipping_option(shipping_cost):
    return {
        "id": "shipping-default",
        "label": "A default shipping option",
        "selected": True,
        "amount": {
            "currency_code": "USD",
            "value": shipping_cost,
        },
    }


def build_purchase_unit(
    partner_id,
    merchant_id,
    price,
    include_shipping_options,
    partner_fee=0,
    reference_id=None,
    include_line_items=True,
    category=None,
    billing_agreement_id=None,
):
    price = float(price)
    purchase_unit = {
        "custom_id": "Up to 127 characters can go here!",
        "payee": {"merchant_id": merchant_id},
        "soft_descriptor": "1234567890111213141516",
    }

    if reference_id is not None:
        purchase_unit["reference_id"] = reference_id

    if partner_fee > 0:
        purchase_unit["payment_instruction"] = {
            "platform_fees": [
                {
                    "amount": {"currency_code": "USD", "value": partner_fee},
                    "payee": {"merchant_id": partner_id},
                }
            ]
        }

    if billing_agreement_id is not None:
        purchase_unit["payment_source"] = {
            "token": {"id": billing_agreement_id, "type": "BILLING_AGREEMENT"}
        }

    breakdown = {}

    if include_shipping_options:
        shipping_cost = 9.99
        shipping_options = [default_shipping_option(shipping_cost)]
        purchase_unit["shipping"] = {"options": shipping_options}
        breakdown["shipping"] = {"currency_code": "USD", "value": shipping_cost}

    if include_line_items:
        match category:
            case "DIGITAL_GOODS":
                name = "A digital good."
            case "DONATION":
                name = "A donation."
            case "PHYSICAL_GOODS":
                name = "A physical good."
            case _:
                category = None
                name = "A good of unspecified category."
        item = {
            "name": name,
            "quantity": 1,
            "unit_amount": {"currency_code": "USD", "value": price},
        }
        if category:
            item["category"] = category
        purchase_unit["items"] = [item]
        breakdown["item_total"] = {"currency_code": "USD", "value": price}

    total_price = round(sum(float(cost["value"]) for cost in breakdown.values()), 2)
    purchase_unit["amount"] = {
        "currency_code": "USD",
        "value": total_price,
        "breakdown": breakdown,
    }
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
    current_app.logger.error(f"form_options = {json.dumps(form_options, indent=2)}")

    headers = build_headers(return_formatted=True)
    formatted = headers["formatted"]
    del headers["formatted"]

    create_response = create_order(headers, form_options)
    formatted["create-order"] = format_request_and_response(create_response)
    try:
        order_id = create_response.json()["id"]
    except KeyError:
        order_id = None

    response_dict = {"formatted": formatted, "orderID": order_id}
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
    partner_fee = float(form_options["partner-fee"])
    category = form_options["category"]
    billing_agreement_id = form_options.get("ba-id") or None  # Coerce to None if empty!
    purchase_unit = build_purchase_unit(
        partner_id=partner_id,
        merchant_id=merchant_id,
        price=price,
        include_shipping_options=include_shipping_options,
        partner_fee=partner_fee,
        category=category,
        billing_agreement_id=billing_agreement_id,
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
    try:
        auth_id = auth_response.json()["purchase_units"][0]["payments"][
            "authorizations"
        ][0]["id"]
    except TypeError as exc:
        current_app.logger.error(
            f"Error accessing auth id from response json: {json.dumps(dict(auth_response.json),indent=2)}"
        )

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
