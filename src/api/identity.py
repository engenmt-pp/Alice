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
def get_client_token():
    """Retrieve a client token using the GET /v1/identity/generate-token endpoint.

    Docs: https://developer.paypal.com/docs/multiparty/checkout/advanced/integrate/#link-generateclienttoken
    """
    endpoint = build_endpoint("/v1/identity/generate-token")

    data = request.get_json()
    auth_header = data.get("auth-header") or None

    client_id = data["partner-client-id"]
    secret = data["partner-secret"]
    bn_code = data["partner-bn-code"]

    if client_id == current_app.config["PARTNER_CLIENT_ID"]:
        secret = current_app.config["PARTNER_SECRET"]
    if client_id == current_app.config["FASTLANE_PARTNER_CLIENT_ID"]:
        secret = current_app.config["FASTLANE_PARTNER_SECRET"]
    if client_id == current_app.config["FASTLANE_MERCHANT_CLIENT_ID"]:
        secret = current_app.config["FASTLANE_MERCHANT_SECRET"]

    headers = build_headers(
        auth_header=auth_header,
        client_id=client_id,
        secret=secret,
        bn_code=bn_code,
    )

    return_val = {}
    formatted = headers.pop("formatted")

    try:
        auth_header = headers["Authorization"]
        return_val["authHeader"] = auth_header
    except KeyError:
        return_val["formatted"] = formatted
        return jsonify(return_val)

    response = requests.post(endpoint, headers=headers)

    formatted["client-token"] = format_request_and_response(response)
    return_val["formatted"] = formatted

    try:
        client_token = response.json()["client_token"]
    except Exception as exc:
        current_app.logger.error(
            f"Exception encountered when getting client_token: {exc}"
        )
    else:
        return_val["clientToken"] = client_token
    finally:
        return jsonify(return_val)


@bp.route("/seller-access-token/", methods=("POST",))
def get_seller_access_token():
    endpoint = build_endpoint("/v1/oauth2/token")
    headers = {
        "Content-Type": "application/json",
        "Accept-Language": "en_US",
    }

    data = request.get_json()

    auth_code = data["auth-code"]
    shared_id = data["shared-id"]
    seller_nonce = data["seller-nonce"]

    payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "code_verifier": seller_nonce,
        "ignoreCache": True,
    }

    response = requests.post(
        endpoint,
        headers=headers,
        data=payload,
        auth=(shared_id, ""),
    )
    formatted = {
        "seller-access-token": format_request_and_response(response),
    }

    access_token = response.json()["access_token"]

    return_val = {
        "formatted": formatted,
        "access_token": access_token,
    }
    return return_val


@bp.route("/seller-credentials/", methods=("POST",))
def get_seller_credentials():
    data = request.get_json()

    partner_id = data["partner-id"]
    endpoint = build_endpoint(
        f"/v1/customer/partners/{partner_id}/merchant-integrations/credentials"
    )

    seller_access_token = data["access-token"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {seller_access_token}",
    }

    response = requests.get(
        endpoint,
        headers=headers,
    )
    formatted = {
        "seller-credentials": format_request_and_response(response),
    }

    return_val = {"formatted": formatted}
    return jsonify(return_val)


@bp.route("/id-token/", defaults={"customer_id": None}, methods=("POST",))
@bp.route("/id-token/<customer_id>", methods=("POST",))
def get_id_token(customer_id):
    """Request access and ID tokens using the GET /v1/oauth2/token endpoint.

    Docs: https://developer.paypal.com/docs/api/reference/get-an-access-token/
    """
    endpoint = build_endpoint("/v1/oauth2/token")
    headers = {"Content-Type": "application/json", "Accept-Language": "en_US"}

    data = request.get_json()

    client_id = data["partner-client-id"]
    secret = data["partner-secret"]

    if client_id == current_app.config["PARTNER_CLIENT_ID"]:
        secret = current_app.config["PARTNER_SECRET"]
    if client_id == current_app.config["FASTLANE_PARTNER_CLIENT_ID"]:
        secret = current_app.config["FASTLANE_PARTNER_SECRET"]
    if client_id == current_app.config["FASTLANE_MERCHANT_CLIENT_ID"]:
        secret = current_app.config["FASTLANE_MERCHANT_SECRET"]

    if request.args.get("include-auth-assertion"):
        # 'include-auth-assertion' is passed in a querystring,
        # so we access with `request.args`.
        merchant_id = data["merchant-id"]
        auth_assertion = build_auth_assertion(client_id, merchant_id)
        headers["PayPal-Auth-Assertion"] = auth_assertion

    data = {
        "ignoreCache": True,
        "grant_type": "client_credentials",
        "response_type": "id_token",
    }

    if customer_id:
        data["target_customer_id"] = customer_id

    response = requests.post(
        endpoint,
        headers=headers,
        data=data,
        auth=(client_id, secret),
    )

    formatted = {"id-token": format_request_and_response(response)}
    return_val = {"formatted": formatted}

    try:
        response_dict = response.json()
        access_token = response_dict["access_token"]
        id_token = response_dict["id_token"]
    except KeyError as exc:
        current_app.logger.error(f"Exception in get_id_token: {exc}")
    else:
        auth_header = f"Bearer {access_token}"
        return_val["authHeader"] = auth_header
        return_val["idToken"] = id_token
    finally:
        return jsonify(return_val)


@bp.route("/sdk-token", methods=("POST",))
def get_sdk_token():
    """Request an SDK token using the GET /v1/oauth2/token endpoint."""

    endpoint = build_endpoint("/v1/oauth2/token")

    data = request.get_json()

    client_id = data["partner-client-id"]
    secret = data["partner-secret"]
    if client_id == current_app.config["PARTNER_CLIENT_ID"]:
        secret = current_app.config["PARTNER_SECRET"]
    if client_id == current_app.config["FASTLANE_PARTNER_CLIENT_ID"]:
        secret = current_app.config["FASTLANE_PARTNER_SECRET"]
    if client_id == current_app.config["FASTLANE_MERCHANT_CLIENT_ID"]:
        secret = current_app.config["FASTLANE_MERCHANT_SECRET"]
    merchant_id = data["merchant-id"]

    data = {
        "grant_type": "client_credentials",
        # "response_type": "sdk_token", # FB: This is in the LR docs but throws an error!
        # "response_type": "token",  # FB: This token is fully scoped!
        "response_type": "client_token",  # FB: This token is limited in scope!
        "intent": "sdk_init",
        "ignoreCache": "true",
        "domains[]": "paypal.com",
    }

    headers = {}
    if request.args.get("include-auth-assertion"):
        # 'include-auth-assertion' is passed in a querystring,
        # so we access with `request.args`.
        auth_assertion = build_auth_assertion(client_id, merchant_id)
        headers["PayPal-Auth-Assertion"] = auth_assertion

    response = requests.post(
        endpoint,
        data=data,
        headers=headers,
        auth=(client_id, secret),
    )

    formatted = {"sdk-token": format_request_and_response(response)}
    return_val = {"formatted": formatted}

    try:
        response_dict = response.json()
        sdk_token = response_dict["access_token"]
    except KeyError as exc:
        current_app.logger.error(f"Exception in get_sdk_token: {exc}")
    else:
        return_val["sdkToken"] = sdk_token
    finally:
        return jsonify(return_val)


def get_access_token(client_id, secret):
    """Request an access token using the /v1/oauth2/token API.

    Docs: https://developer.paypal.com/docs/api/reference/get-an-access-token/
    """
    endpoint = build_endpoint("/v1/oauth2/token")
    headers = {
        "Content-Type": "application/json",
        "Accept-Language": "en_US",
    }
    data = {
        "grant_type": "client_credentials",
        "ignoreCache": True,
    }

    response = requests.post(
        endpoint,
        headers=headers,
        data=data,
        auth=(client_id, secret),
    )

    formatted = {"access-token": format_request_and_response(response)}
    return_val = {"formatted": formatted}

    try:
        access_token = response.json()["access_token"]
    except KeyError as exc:
        current_app.logger.error(f"Encountered a KeyError: {exc}")
    else:
        return_val["access_token"] = access_token
    finally:
        return return_val


def build_auth_assertion(client_id, merchant_id):
    """Build and return the PayPal Auth Assertion.

    Docs: https://developer.paypal.com/docs/api/reference/api-requests/#paypal-auth-assertion
    """
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
    merchant_id=None,
    include_request_id=False,
    auth_header=None,
):
    """Build commonly used headers using a new PayPal access token."""

    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
        "Content-Type": "application/json",
        "formatted": {},
    }

    if not auth_header:
        if client_id is None or secret is None:
            raise Exception(
                f"Invalid client ID/secret passed:\n{client_id=}\n{secret=}"
            )
        access_token_response = get_access_token(client_id, secret)
        headers["formatted"] |= access_token_response["formatted"]
        try:
            access_token = access_token_response["access_token"]
        except KeyError as exc:
            current_app.logger.error(
                f"<build_headers> Encountered Exception accessing access_token: {exc}"
            )
            return headers
        else:
            auth_header = f"Bearer {access_token}"

    headers["Authorization"] = auth_header

    if include_request_id:
        request_id = random_decimal_string(10)
        headers["PayPal-Request-Id"] = request_id

    if bn_code is not None:
        headers["PayPal-Partner-Attribution-Id"] = bn_code

    if merchant_id:
        auth_assertion = build_auth_assertion(client_id, merchant_id)
        headers["PayPal-Auth-Assertion"] = auth_assertion

    return headers
