import requests

from flask import Blueprint, current_app, jsonify, request
from .utils import (
    build_endpoint,
    format_request_and_response,
)
from .identity import build_headers

bp = Blueprint("billing_agreements", __name__, url_prefix="/billing-agreements")


@bp.route("/<baid>", methods=("POST",))
def get_ba_status(baid):
    current_app.logger.error(f"Called get_ba_status with {baid=}")
    endpoint = build_endpoint(f"/v1/billing-agreements/agreements/{baid}")

    headers = build_headers(
        include_auth_assertion=True, return_formatted=True, auth_header=None
    )
    formatted = headers["formatted"]
    del headers["formatted"]

    status_response = requests.get(endpoint, headers=headers)
    formatted["ba-status"] = format_request_and_response(status_response)

    response_dict = {"formatted": formatted}

    return jsonify(response_dict)
