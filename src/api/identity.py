import base64
import json
import requests

from flask import Blueprint, current_app, jsonify, request
from .utils import (
    build_endpoint,
    log_and_request,
    format_request_and_response,
    random_decimal_string,
)


bp = Blueprint("identity", __name__, url_prefix="/identity")


def generate_client_token(customer_id=None, return_formatted=False):
    endpoint = build_endpoint("/v1/identity/generate-token")
    headers = build_headers(return_formatted=return_formatted)
    if return_formatted:
        formatted = headers["formatted"]
        del headers["formatted"]

    if customer_id:
        data = {"customer_id": customer_id}
        response = log_and_request("POST", endpoint, headers=headers, data=data)
    else:
        response = requests.post(endpoint, headers=headers)

    client_token = response.json()["client_token"]
    response_dict = {"client-token": client_token}

    if return_formatted:
        formatted["client-token"] = format_request_and_response(response)
        response_dict["formatted"] = formatted

    return jsonify(response_dict)


@bp.route("/id-token/", defaults={"customer_id": None}, methods=("GET",))
@bp.route("/id-token/<customer_id>", methods=("GET",))
@bp.route("/id-token-with-auth/", defaults={"customer_id": None}, methods=("GET",))
@bp.route("/id-token-with-auth/<customer_id>", methods=("GET",))
def get_id_token(customer_id):
    """Request access and ID tokens using the /v1/oauth2/token API.

    Docs: https://developer.paypal.com/docs/api/reference/get-an-access-token/
    """
    endpoint = build_endpoint("/v1/oauth2/token")
    headers = {"Content-Type": "application/json", "Accept-Language": "en_US"}

    if "id-token-with-auth/" in request.path:
        auth_assertion = build_auth_assertion()
        headers["PayPal-Auth-Assertion"] = auth_assertion

    data = {
        "ignoreCache": True,
        "grant_type": "client_credentials",
        "response_type": "id_token",
    }

    if customer_id:
        data["target_customer_id"] = customer_id

    client_id = current_app.config["PARTNER_CLIENT_ID"]
    secret = current_app.config["PARTNER_SECRET"]

    response = requests.post(
        endpoint, headers=headers, data=data, auth=(client_id, secret)
    )
    response_dict = response.json()

    formatted = {"access-token": format_request_and_response(response)}
    return_val = {"formatted": formatted}
    try:
        access_token = response_dict["access_token"]
        id_token = response_dict["id_token"]
    except KeyError:
        return return_val

    auth_header = f"Bearer {access_token}"
    return_val["auth-header"] = auth_header
    return_val["id-token"] = id_token

    return jsonify(return_val)


def request_access_token(client_id, secret, return_formatted=False):
    """Request an access token using the /v1/oauth2/token API.

    Docs: https://developer.paypal.com/docs/api/reference/get-an-access-token/
    """
    endpoint = build_endpoint("/v1/oauth2/token")
    headers = {"Content-Type": "application/json", "Accept-Language": "en_US"}

    data = {"grant_type": "client_credentials", "ignoreCache": True}

    response = requests.post(
        endpoint, headers=headers, data=data, auth=(client_id, secret)
    )
    response_dict = response.json()

    try:
        access_token = response_dict["access_token"]
        return_val = {"access_token": access_token}
        if return_formatted:
            formatted = format_request_and_response(response)
            return_val["formatted"] = formatted
        return return_val
    except KeyError as exc:
        current_app.logger.error(f"Encountered a KeyError: {exc}")
        current_app.logger.error(
            f"response_dict = {json.dumps(response_dict, indent=2)}"
        )
        raise exc


def build_auth_assertion(client_id=None, merchant_id=None):
    """Build and return the PayPal Auth Assertion.

    Docs: https://developer.paypal.com/docs/api/reference/api-requests/#paypal-auth-assertion
    """
    client_id = client_id or current_app.config["PARTNER_CLIENT_ID"]
    merchant_id = merchant_id or current_app.config["MERCHANT_ID"]

    header = {"alg": "none"}
    header_b64 = base64.b64encode(json.dumps(header).encode("ascii"))

    payload = {"iss": client_id, "payer_id": merchant_id}
    payload_b64 = base64.b64encode(json.dumps(payload).encode("ascii"))

    signature = b""
    return b".".join([header_b64, payload_b64, signature])


def build_headers(
    client_id=None,
    secret=None,
    bn_code=None,
    include_bn_code=True,
    include_auth_assertion=False,
    include_request_id=False,
    return_formatted=False,
    auth_header=None,
):
    """Build commonly used headers using a new PayPal access token."""

    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
        "Content-Type": "application/json",
    }

    if auth_header is None:
        client_id = client_id or current_app.config["PARTNER_CLIENT_ID"]
        secret = secret or current_app.config["PARTNER_SECRET"]

        access_token_response = request_access_token(
            client_id, secret, return_formatted=return_formatted
        )
        access_token = access_token_response["access_token"]
        auth_header = f"Bearer {access_token}"
        if return_formatted:
            formatted = {"access-token": access_token_response["formatted"]}
            headers["formatted"] = formatted

    headers["Authorization"] = auth_header

    if include_request_id:
        request_id = random_decimal_string(10)
        headers["PayPal-Request-Id"] = request_id

    if include_bn_code:
        bn_code = bn_code or current_app.config["PARTNER_BN_CODE"]
        headers["PayPal-Partner-Attribution-Id"] = bn_code

    if include_auth_assertion:
        auth_assertion = build_auth_assertion()
        headers["PayPal-Auth-Assertion"] = auth_assertion

    return headers
