from flask import Blueprint, current_app, jsonify, request

import json

from .utils import (
    build_endpoint,
    log_and_request,
    format_request_and_response,
)

from .identity import build_headers

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
    tax,
    partner_fee=0,
    include_payee=True,
    include_line_items=True,
    include_shipping_options=False,
    include_shipping_address=False,
    custom_id=None,
    reference_id=None,
    item_category=None,
    soft_descriptor=None,
    disbursement_mode=None,
    billing_agreement_id=None,
):
    price = float(price)
    tax = float(tax)

    purchase_unit = dict()

    if include_payee:
        purchase_unit["payee"] = {"merchant_id": merchant_id}
    if reference_id:
        purchase_unit["reference_id"] = reference_id
    if custom_id:
        purchase_unit["custom_id"] = custom_id
    if soft_descriptor:
        purchase_unit["soft_descriptor"] = soft_descriptor

    if partner_fee > 0:
        payment_instruction = {
            "platform_fees": [
                {
                    "amount": {"currency_code": "USD", "value": partner_fee},
                    "payee": {"merchant_id": partner_id},
                }
            ]
        }
        purchase_unit["payment_instruction"] = payment_instruction

    if billing_agreement_id:
        payment_source = {
            "token": {"id": billing_agreement_id, "type": "BILLING_AGREEMENT"}
        }
        purchase_unit["payment_source"] = payment_source

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
        if tax:
            tax_amount = {"currency_code": "USD", "value": tax}
            item["tax"] = tax_amount
            breakdown["tax_total"] = tax_amount
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


def build_context(shipping_preference):
    context = {
        "return_url": "http://localhost:5000/",
        "cancel_url": "http://localhost:5000/",
    }
    if shipping_preference:
        context["shipping_preference"] = shipping_preference
    return context


@bp.route("/create", methods=("POST",))
def create_order_router():
    """Create an order with the /v2/checkout/orders API.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    form_options = request.get_json()
    current_app.logger.debug(f"form_options = {json.dumps(form_options, indent=2)}")

    auth_header = form_options.get("authHeader")
    return_formatted = auth_header is None

    vaulting_v3 = form_options.get("vault-v3", "")
    if vaulting_v3 == "merchant":
        include_auth_assertion = True
    else:
        include_auth_assertion = False

    headers = build_headers(
        return_formatted=return_formatted,
        auth_header=auth_header,
        include_auth_assertion=include_auth_assertion,
        include_request_id=True,
    )
    if return_formatted:
        formatted = headers["formatted"]
        del headers["formatted"]
    else:
        formatted = {}

    if auth_header is None:
        auth_header = headers["Authorization"]

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
    tax = form_options["tax"]
    vault_v3 = form_options.get("vault-v3")
    vault_v3_id = form_options.get("vault-id")
    include_payee = vault_v3 != "merchant"
    include_shipping_options = form_options.get("include-shipping-options")
    include_shipping_address = form_options.get("include-shipping-address")
    reference_id = form_options.get("reference-id")
    custom_id = form_options.get("custom-id")
    soft_descriptor = form_options.get("soft-descriptor")

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
        tax=tax,
        partner_fee=partner_fee,
        include_payee=include_payee,
        include_shipping_options=include_shipping_options,
        include_shipping_address=include_shipping_address,
        custom_id=custom_id,
        reference_id=reference_id,
        item_category=item_category,
        soft_descriptor=soft_descriptor,
        # disbursement_mode=disbursement_mode,
        billing_agreement_id=billing_agreement_id,
    )

    context = build_context(shipping_preference)

    data = {
        "intent": intent,
        "purchase_units": [purchase_unit],
    }

    payment_source = {
        "paypal": {
            "experience_context": context,
        },
    }
    if vault_v3_id:
        payment_source["paypal"]["vault_id"] = vault_v3_id
    elif vault_v3:
        payment_source["paypal"]["attributes"] = {
            "vault": {
                "store_in_vault": "ON_SUCCESS",
                "usage_type": vault_v3.upper(),
            }
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
    current_app.logger.debug(f"form_options = {json.dumps(form_options, indent=2)}")

    auth_header = form_options["auth-header"]
    include_auth_assertion = form_options.get("vault-v3") == "merchant"
    headers = build_headers(
        auth_header=auth_header, include_auth_assertion=include_auth_assertion
    )

    intent = form_options["intent"]
    if intent == "AUTHORIZE":
        formatted_dict = auth_and_capture_order(order_id, form_options, headers)
    else:
        capture_response = capture_order(order_id, headers)
        formatted_dict = {
            "capture-order": format_request_and_response(capture_response)
        }

    return jsonify({"formatted": formatted_dict})


def auth_and_capture_order(order_id, form_options, headers):
    """Authorize and then capture the order according to the provided form options.

    Return a dictionary of the formatted requests and responses.
    """
    auth_response = authorize_order(order_id, headers)
    formatted_dict = {"authorize-order": format_request_and_response(auth_response)}
    try:
        auth_id = auth_response.json()["purchase_units"][0]["payments"][
            "authorizations"
        ][0]["id"]
    except (TypeError, IndexError) as exc:
        current_app.logger.error(
            f"Error accessing auth id from response json: {json.dumps(dict(auth_response.json()),indent=2)}"
        )
        return formatted_dict

    capture_response = capture_authorization(auth_id, form_options, headers)
    formatted_dict["capture-order"] = format_request_and_response(capture_response)
    return formatted_dict


def authorize_order(order_id, headers):
    """Authorize the order using the /v2/checkout/orders API.

    Returns the response object.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_authorize
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}/authorize")

    response = log_and_request("POST", endpoint, headers=headers)
    return response


def capture_order(order_id, headers):
    """Capture the order with the /v2/checkout/orders API.

    Returns the response object.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}/capture")

    response = log_and_request("POST", endpoint, headers=headers)
    return response


def capture_authorization(auth_id, form_options, headers):
    """Capture the authorization with the given `auth_id` using the /v2/payments API.

    Returns the response object.

    Docs: https://developer.paypal.com/docs/api/payments/v2/#authorizations_capture
    """
    endpoint = build_endpoint(f"/v2/payments/authorizations/{auth_id}/capture")

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

    auth_header = request.args.get("auth-header")
    headers = build_headers(auth_header=auth_header)

    response = log_and_request("GET", endpoint, headers=headers)
    formatted = {"get-order": format_request_and_response(response)}
    response_dict = {"formatted": formatted}
    return jsonify(response_dict)
