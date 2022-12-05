from flask import Blueprint, current_app, jsonify, request

from .utils import (
    build_endpoint,
    build_headers,
    log_and_request,
    format_request_and_response,
)

bp = Blueprint("billing_form", __name__, url_prefix="/billing-form")


def default_billing_agreement():
    return {
        "description": "A billing agreement.",
        "shipping_address": {
            "line1": "1324 Permutation Parkway",
            "city": "Gainesville",
            "state": "FL",
            "postal_code": "32601",
            "country_code": "US",
            "recipient_name": "John Doe",
        },
        "payer": {"payment_method": "PAYPAL"},
        "plan": {
            "type": "CHANNEL_INITIATED_BILLING",
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
    endpoint = build_endpoint("/v1/billing-agreements/agreement-tokens")

    headers = build_headers(return_formatted=True)
    formatted = {"access-token": headers["formatted"]}
    del headers["formatted"]

    data = default_billing_agreement()

    create_response = log_and_request("POST", endpoint, headers=headers, data=data)
    formatted["create-billing-agreement"] = format_request_and_response(create_response)

    token_id = create_response.json()["token_id"]
    response_dict = {"formatted": formatted, "tokenId": token_id}
    return jsonify(response_dict)
