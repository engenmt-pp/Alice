import requests

from flask import Blueprint, current_app, jsonify, request
from .utils import build_endpoint, format_request_and_response
from .identity import build_headers

bp = Blueprint("billing_agreements", __name__, url_prefix="/billing-agreements")


@bp.route("/<baid>", methods=("POST",))
def get_ba_status(baid):
    data = request.json()

    client_id = data.get("partner-client-id")
    secret = data.get("partner-secret")
    bn_code = data.get("partner-bn-code")
    merchant_id = data.get("merchant-id")

    if client_id == current_app.config["PARTNER_CLIENT_ID"]:
        secret = current_app.config["PARTNER_SECRET"]

    current_app.logger.info(f"Getting the status of a billing agreement with {baid=}")

    endpoint = build_endpoint(f"/v1/billing-agreements/agreements/{baid}")
    headers = build_headers(
        client_id=client_id,
        secret=secret,
        bn_code=bn_code,
        merchant_id=merchant_id,
    )
    formatted = headers.pop("formatted")

    status_response = requests.get(endpoint, headers=headers)
    formatted["ba-status"] = format_request_and_response(status_response)

    return_val = {"formatted": formatted}

    return jsonify(return_val)
