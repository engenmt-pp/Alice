from flask import Blueprint, current_app, jsonify, request

from .utils import (
    build_endpoint,
    build_headers,
    log_and_request,
    format_request_and_response,
)

bp = Blueprint("billing_form", __name__, url_prefix="/billing-form")


def default_billing_agreement(type=None):
    if type and type.upper() == "MIB":
        type = "MERCHANT_INITIATED_BILLING"
    else:
        type = "CHANNEL_INITIATED_BILLING"
    return {
        "description": "A billing agreement.",
        "shipping_address": {
            "line1": "1324 Permutation Pattern Parkway",
            "city": "Gainesville",
            "state": "FL",
            "postal_code": "32601",
            "country_code": "US",
            "recipient_name": "John Doe",
        },
        "payer": {"payment_method": "PAYPAL"},
        "plan": {
            "type": type,
            "merchant_preferences": {
                "return_url": "https://example.com/return",
                "cancel_url": "https://example.com/cancel",
                "notify_url": "https://example.com/notify",
                "accepted_pymt_type": "INSTANT",
                "skip_shipping_address": False,
                "immutable_shipping_address": True,
            },
        },
    }


@bp.route("/create-billing-agreement-token", methods=("POST",))
def create_billing_agreement_token():
    form_options = request.get_json()
    ba_type = form_options.get("ba-type", "CIB")

    endpoint = build_endpoint("/v1/billing-agreements/agreement-tokens")
    api_caller = form_options.get("api-caller", "partner")
    headers = build_headers(
        api_caller=api_caller,
        include_bn_code=True,
        include_auth_assertion=True,
        return_formatted=True,
    )
    formatted = headers["formatted"]
    del headers["formatted"]

    data = default_billing_agreement(type=ba_type)

    create_response = log_and_request("POST", endpoint, headers=headers, data=data)
    formatted["create-billing-agreement-token"] = format_request_and_response(
        create_response
    )

    token_id = create_response.json().get("token_id")

    response_dict = {"formatted": formatted, "tokenId": token_id}
    return jsonify(response_dict)


@bp.route("/create-billing-agreement", methods=("POST",))
def create_billing_agreement():
    form_options = request.get_json()

    endpoint = build_endpoint("/v1/billing-agreements/agreements")
    api_caller = form_options.get("api-caller", "partner")
    headers = build_headers(
        api_caller=api_caller,
        include_bn_code=False,
        include_auth_assertion=True,
        return_formatted=True,
    )
    formatted = headers["formatted"]
    del headers["formatted"]

    ba_token = request.get_json()["ba-token"]
    data = {"token_id": ba_token}

    create_response = log_and_request("POST", endpoint, headers=headers, data=data)
    formatted["create-billing-agreement"] = format_request_and_response(create_response)

    ba_id = create_response.json().get("id")

    response_dict = {"formatted": formatted, "billingAgreementID": ba_id}
    return jsonify(response_dict)
