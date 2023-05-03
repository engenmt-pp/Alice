from flask import Blueprint, current_app, jsonify, request

from .utils import (
    build_endpoint,
    log_and_request,
    format_request_and_response,
)
from .identity import build_headers

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
    headers = build_headers(include_auth_assertion=True, return_formatted=True)
    formatted = headers["formatted"]
    auth_header = headers["Authorization"]
    del headers["formatted"]

    data = default_billing_agreement()

    create_response = log_and_request("POST", endpoint, headers=headers, data=data)
    formatted["create-billing-agreement-token"] = format_request_and_response(
        create_response
    )

    token_id = create_response.json().get("token_id")

    response_dict = {
        "formatted": formatted,
        "tokenId": token_id,
        "authHeader": auth_header,
    }
    return jsonify(response_dict)


@bp.route("/create-billing-agreement", methods=("POST",))
def create_billing_agreement():
    endpoint = build_endpoint("/v1/billing-agreements/agreements")

    form_options = request.get_json()
    auth_header = form_options["authHeader"]
    headers = build_headers(include_auth_assertion=True, auth_header=auth_header)

    ba_token = form_options["ba-token"]
    data = {"token_id": ba_token}

    create_response = log_and_request("POST", endpoint, headers=headers, data=data)
    formatted = {
        "create-billing-agreement": format_request_and_response(create_response)
    }
    ba_id = create_response.json().get("id")

    response_dict = {"formatted": formatted, "billingAgreementID": ba_id}
    return jsonify(response_dict)


# @bp.route("/status")
# @bp.route("/status/<baid>")
@bp.route("/status/<baid>", methods=("POST",))
def billing_agreement_status(baid):
    current_app.logger.error(f"Called billing_agreement_status with {baid=}")
    endpoint = build_endpoint(f"/v1/billing-agreements/agreements/{baid}")

    # form_options = request.get_json()
    # auth_header = form_options.get("authHeader")
    headers = build_headers(
        include_auth_assertion=True, return_formatted=True, auth_header=None
    )
    formatted = headers["formatted"]
    del headers["formatted"]

    status_response = log_and_request("GET", endpoint, headers=headers)
    formatted["ba-status"] = format_request_and_response(status_response)

    response_dict = {"formatted": formatted}

    return jsonify(response_dict)
