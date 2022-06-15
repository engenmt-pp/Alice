import base64
import json
import requests


from flask import current_app
from urllib.parse import urlencode


def build_endpoint(route, query=None):
    """Build the appropriate API endpoint given the suffix/route."""
    endpoint_prefix = current_app.config["ENDPOINT_PREFIX"]
    endpoint = f"{endpoint_prefix}{route}"
    if query is None:
        return endpoint

    query_string = urlencode(query)
    return f"{endpoint}?{query_string}"


def log_and_request(method, endpoint, **kwargs):
    """Log and make the HTTP request, and then log and return the response."""
    methods_dict = {
        "GET": requests.get,
        "PATCH": requests.patch,
        "POST": requests.post,
    }
    if method not in methods_dict:
        raise Exception(f"HTTP request method '{method}' not recognized!")

    try:
        kwargs_str = json.dumps(kwargs, indent=2)
    except TypeError:
        kwargs_str = str(kwargs)

    current_app.logger.debug(f"\nSending {method} request to {endpoint}:\n{kwargs_str}")

    if "data" in kwargs:
        kwargs["data"] = json.dumps(kwargs["data"])

    response = methods_dict[method](endpoint, **kwargs)
    try:
        response_str = json.dumps(response.json(), indent=2)
    except json.decoder.JSONDecodeError:
        response_str = response.text

    if not response.ok:
        current_app.logger.error(f"{response.status_code} Error: {response_str}\n\n")
    else:
        current_app.logger.debug(f"{response.status_code} Response: {response_str}\n\n")

    return response


def request_access_token(client_id, secret):
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
        return response_dict["access_token"]
    except KeyError as exc:
        current_app.logger.error(f"Encountered a KeyError: {exc}")
        current_app.logger.error(
            f"response_dict = {json.dumps(response_dict, indent=2)}"
        )
        raise exc


def build_headers(
    client_id=None, secret=None, include_bn_code=False, include_auth_assertion=False
):
    """Build commonly used headers using a new PayPal access token."""
    if client_id is None:
        client_id = current_app.config["PARTNER_CLIENT_ID"]
    if secret is None:
        secret = current_app.config["PARTNER_SECRET"]

    access_token = request_access_token(client_id, secret)
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    if include_bn_code:
        headers["PayPal-Partner-Attribution-Id"] = current_app.config["PARTNER_BN_CODE"]

    if include_auth_assertion:
        headers["PayPal-Auth-Assertion"] = build_auth_assertion()

    return headers


def build_auth_assertion(client_id=None, merchant_id=None):
    """Build and return the PayPal Auth Assertion.

    Docs: https://developer.paypal.com/docs/api/reference/api-requests/#paypal-auth-assertion
    """
    if client_id is None:
        client_id = current_app.config["PARTNER_CLIENT_ID"]
    if merchant_id is None:
        merchant_id = current_app.config["MERCHANT_ID"]

    header = {"alg": "none"}
    header_b64 = base64.b64encode(json.dumps(header).encode("ascii"))

    payload = {"iss": client_id, "payer_id": merchant_id}
    payload_b64 = base64.b64encode(json.dumps(payload).encode("ascii"))

    signature = b""
    return b".".join([header_b64, payload_b64, signature])


def generate_client_token(customer_id=None):
    endpoint = build_endpoint("/v1/identity/generate-token")
    headers = build_headers()

    if customer_id is None:
        response = requests.post(endpoint, headers=headers)
    else:
        data = {"customer_id": customer_id}
        data_str = json.dumps(data)
        response = requests.post(endpoint, headers=headers, data=data_str)

    response_dict = response.json()
    return response_dict["client_token"]
