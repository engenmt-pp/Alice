import base64
import json
import requests

from flask import Blueprint, current_app, jsonify, request
from .utils import (
    build_endpoint,
    format_request_and_response,
    random_decimal_string,
)


bp = Blueprint("identity", __name__, url_prefix="/identity")


@bp.route("/client-token", methods=("POST",))
def generate_client_token(auth_header=None):
    data = request.get_json()
    auth_header = data.get("authHeader")

    current_app.logger.info(f"Client token with {auth_header=}")

    endpoint = build_endpoint("/v1/identity/generate-token")
    headers = build_headers(return_formatted=True, auth_header=auth_header)

    auth_header = auth_header or headers["Authorization"]
    response_dict = {"authHeader": auth_header}

    # The `headers` response may not have any formatted calls, so default to the empty dict.
    formatted = headers.get("formatted", dict())
    headers.pop("formatted", None)

    response = requests.post(endpoint, headers=headers)

    formatted["client-token"] = format_request_and_response(response)
    response_dict["formatted"] = formatted

    try:
        client_token = response.json()["client_token"]
        response_dict["clientToken"] = client_token
    except Exception as exc:
        current_app.logger.error(
            f"Exception encountered when getting client_token: {exc}"
        )

    return jsonify(response_dict)


@bp.route("/id-token/", defaults={"customer_id": None}, methods=("GET",))
@bp.route("/id-token/<customer_id>", methods=("GET",))
def get_id_token(customer_id):
    """Request access and ID tokens using the /v1/oauth2/token API.

    Docs: https://developer.paypal.com/docs/api/reference/get-an-access-token/
    """
    endpoint = build_endpoint("/v1/oauth2/token")
    headers = {"Content-Type": "application/json", "Accept-Language": "en_US"}

    if request.args.get("include-auth-assertion"):
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
    return_val["authHeader"] = auth_header
    return_val["idToken"] = id_token

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

    if not auth_header:
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
