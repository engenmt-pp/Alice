import json
import requests

from flask import Blueprint, current_app, jsonify, request
from .utils import (
    build_endpoint,
    format_request_and_response,
)
from .identity import build_headers

bp = Blueprint("vault", __name__, url_prefix="/vault")


@bp.route("/<vault_id>", methods=("POST",))
def get_vault_id_status(vault_id):
    data = request.get_json()
    # data['vault-id'] = vault_id
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.debug(
        f"Getting the status of a vault ID with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    include_auth_assertion = bool(data.get("include-auth-assertion", False))
    auth_header = data.get("authHeader")

    endpoint = build_endpoint(f"/v3/vault/payment-tokens/{vault_id}")
    headers = build_headers(
        include_auth_assertion=include_auth_assertion,
        return_formatted=True,
        auth_header=auth_header,
    )
    formatted = {}
    if "formatted" in headers:
        formatted |= headers["formatted"]
        del headers["formatted"]

    auth_header = headers["Authorization"]
    response_dict = {"authHeader": auth_header}

    response = requests.get(endpoint, headers=headers)
    formatted["vault-status"] = format_request_and_response(response)

    response_dict["formatted"] = formatted

    return jsonify(response_dict)


@bp.route("/customers/<customer_id>", methods=("POST",))
def get_vault_tokens(customer_id):
    data = request.get_json()
    # data['vault-id'] = vault_id
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.debug(
        f"Listing the vault tokens of a customer with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    include_auth_assertion = bool(data.get("include-auth-assertion", False))
    auth_header = data.get("authHeader")

    endpoint = build_endpoint(
        f"/v3/vault/payment-tokens", query={"customer_id": customer_id}
    )
    headers = build_headers(
        include_auth_assertion=include_auth_assertion,
        return_formatted=True,
        auth_header=auth_header,
    )
    formatted = {}
    if "formatted" in headers:
        formatted |= headers["formatted"]
        del headers["formatted"]

    auth_header = headers["Authorization"]
    response_dict = {"authHeader": auth_header}

    response = requests.get(endpoint, headers=headers)
    formatted["vault-tokens"] = format_request_and_response(response)

    response_dict["formatted"] = formatted

    return jsonify(response_dict)
