from flask import Blueprint, current_app, jsonify, request

import json

from .utils import (
    build_endpoint,
    build_headers,
    log_and_request,
    format_request_and_response,
    random_decimal_string,
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


def build_shipping(include_shipping_address, include_shipping_options, shipping_cost):
    if include_shipping_address:
        shipping = {
            "type": "SHIPPING",
            "name": {"full_name": "Trogdor"},
            "address": {
                "address_line_1": "1324 Permutation Parkway",
                "admin_area_2": "Gainesville",
                "admin_area_1": "FL",
                "postal_code": "32601",
                "country_code": "US",
            },
        }
    else:
        shipping = {}

    if include_shipping_options:
        shipping_options = [default_shipping_option(shipping_cost)]
        shipping["options"] = shipping_options

    return shipping


def build_purchase_unit(
    partner_id,
    merchant_id,
    price,
    include_shipping_options,
    include_shipping_address,
    disbursement_mode=None,
    partner_fee=0,
    reference_id=None,
    include_line_items=True,
    item_category=None,
    billing_agreement_id=None,
    include_payee=True,
):
    price = float(price)
    purchase_unit = {
        "custom_id": "Up to 127 characters can go here!",
        "soft_descriptor": "1234567890111213141516",
    }
    if include_payee:
        purchase_unit["payee"] = {"merchant_id": merchant_id}

    if reference_id is not None:
        purchase_unit["reference_id"] = reference_id

    if partner_fee > 0:
        payment_instruction = {}
        payment_instruction["platform_fees"] = [
            {
                "amount": {"currency_code": "USD", "value": partner_fee},
                "payee": {"merchant_id": partner_id},
            }
        ]
        purchase_unit["payment_instruction"] = payment_instruction

    breakdown = {}
    shipping_cost = 9.99
    shipping = build_shipping(
        include_shipping_address=include_shipping_address,
        include_shipping_options=include_shipping_options,
        shipping_cost=shipping_cost,
    )
    if shipping:
        purchase_unit["shipping"] = shipping
    if include_shipping_options:
        breakdown["shipping"] = {"currency_code": "USD", "value": shipping_cost}

    if include_line_items:
        match item_category:
            case "PHYSICAL_GOODS":
                name = "A physical good."
            case "DIGITAL_GOODS":
                name = "A digital good."
            case "DONATION":
                name = "A donation."
            case _:
                item_category = None
                name = "A good of unspecified category."
        item = {
            "name": name,
            "quantity": 1,
            "unit_amount": {"currency_code": "USD", "value": price},
        }
        if item_category:
            item["category"] = item_category
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
    application_context = {
        "return_url": "http://localhost:5000/",
        "cancel_url": "http://localhost:5000/",
    }
    if shipping_preference:
        application_context["shipping_preference"] = shipping_preference
    return application_context


@bp.route("/create", methods=("POST",))
def create_order_router():
    """Create an order with the /v2/checkout/orders API.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    form_options = request.get_json()
    current_app.logger.error(f"form_options = {json.dumps(form_options, indent=2)}")

    headers = build_headers(return_formatted=True, include_auth_assertion=False)
    formatted = headers["formatted"]
    del headers["formatted"]
    headers["PayPal-Request-Id"] = random_decimal_string(length=10)

    create_response = create_order(headers, form_options)
    formatted["create-order"] = format_request_and_response(create_response)
    try:
        order_id = create_response.json()["id"]
    except KeyError:
        order_id = None

    response_dict = {
        "formatted": formatted,
        "orderID": order_id,
        "authHeader": auth_header,
    }
    return jsonify(response_dict)


def create_order(headers, form_options):
    """Create an order with the /v2/checkout/orders API.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")

    intent = form_options["intent"]

    shipping_preference = form_options["shipping-preference"]
    partner_id = form_options["partner-id"]
    merchant_id = form_options["merchant-id"]
    price = form_options["price"]
    include_shipping_options = form_options.get("include-shipping-options")
    include_shipping_address = form_options.get("include-shipping-address")

    if "PayPal-Auth-Assertion" in headers:
        include_payee = False
    else:
        include_payee = True

    if intent == "CAPTURE":
        partner_fee = float(form_options["partner-fee"])
        disbursement_mode = form_options["disbursement-mode"]
    else:
        # Both partner fee and disbursement mode should be delayed until capture for 'intent: authorize' orders.
        partner_fee = 0
        disbursement_mode = None

    item_category = form_options["item-category"]
    billing_agreement_id = form_options.get("ba-id") or None  # Coerce to None if empty!
    purchase_unit = build_purchase_unit(
        partner_id=partner_id,
        merchant_id=merchant_id,
        price=price,
        disbursement_mode=disbursement_mode,
        include_shipping_options=include_shipping_options,
        include_shipping_address=include_shipping_address,
        partner_fee=partner_fee,
        item_category=item_category,
        include_payee=include_payee,
    )

    application_context = build_application_context(shipping_preference)

    data = {
        "application_context": application_context,
        "intent": intent,
        "purchase_units": [purchase_unit],
    }
    if billing_agreement_id:
        payment_source = {
            "token": {"id": billing_agreement_id, "type": "BILLING_AGREEMENT"}
        }
        data["payment_source"] = payment_source

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    return response


@bp.route("/capture/<order_id>", methods=("POST",))
def capture_order_router(order_id):
    """Capture the order with the /v2/checkout/orders API.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
    """
    form_options = request.get_json()
    current_app.logger.error(f"form_options = {json.dumps(form_options, indent=2)}")

    auth_header = form_options["authHeader"]
    intent = form_options["intent"]
    if intent == "AUTHORIZE":
        formatted_dict = auth_and_capture_order(
            order_id, form_options, auth_header=auth_header
        )
    else:
        capture_response = capture_order(order_id, auth_header=auth_header)
        formatted_dict = {
            "capture-order": format_request_and_response(capture_response)
        }

    return jsonify({"formatted": formatted_dict})


def auth_and_capture_order(order_id, form_options, auth_header):
    """Authorize and then capture the order according to the provided form options.

    Return a dictionary of the formatted requests and responses.
    """
    auth_response = authorize_order(order_id, auth_header=auth_header)
    formatted_dict = {"authorize-order": format_request_and_response(auth_response)}
    try:
        auth_id = auth_response.json()["purchase_units"][0]["payments"][
            "authorizations"
        ][0]["id"]
    except (TypeError, KeyError) as exc:
        current_app.logger.error(
            f"Error accessing auth id from response json: {json.dumps(dict(auth_response.json()),indent=2)}"
        )
        return formatted_dict

    capture_response = capture_authorization(
        auth_id, form_options, auth_header=auth_header
    )
    formatted_dict["capture-order"] = format_request_and_response(capture_response)
    return formatted_dict


def authorize_order(order_id, auth_header):
    """Authorize the order using the /v2/checkout/orders API.

    Returns the response object.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_authorize
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}/authorize")
    headers = build_headers(auth_header=auth_header)

    response = log_and_request("POST", endpoint, headers=headers)
    return response


def capture_order(order_id, auth_header):
    """Capture the order with the /v2/checkout/orders API.

    Returns the response object.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}/capture")
    headers = build_headers(auth_header=auth_header)

    response = log_and_request("POST", endpoint, headers=headers)
    return response


def capture_authorization(auth_id, form_options, auth_header):
    """Capture the authorization with the given `auth_id` using the /v2/payments API.

    Returns the response object.

    Docs: https://developer.paypal.com/docs/api/payments/v2/#authorizations_capture
    """
    endpoint = build_endpoint(f"/v2/payments/authorizations/{auth_id}/capture")
    headers = build_headers(auth_header=auth_header)

    partner_fee = float(form_options["partner-fee"])
    disbursement_mode = form_options["disbursement-mode"]

    data = dict()
    payment_instruction = dict()
    if disbursement_mode == "DELAYED":
        payment_instruction["disbursement_mode"] = disbursement_mode
    if partner_fee > 0:
        payment_instruction["platform_fees"] = [
            {"amount": {"currency_code": "USD", "value": partner_fee}}
        ]
    if payment_instruction:
        data["payment_instruction"] = payment_instruction

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    return response


@bp.route("/status/<order_id>", methods=("GET",))
def get_order_status(order_id):
    """Get the status of the order with the /v2/checkout/orders API.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_get
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}")

    auth_header = request.args.get("authHeader")
    headers = build_headers(auth_header=auth_header)

    response = log_and_request("GET", endpoint, headers=headers)
    formatted = {"get-order": format_request_and_response(response)}
    response_dict = {"formatted": formatted}
    return jsonify(response_dict)
