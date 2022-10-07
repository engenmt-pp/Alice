import base64
import json
import random
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

    bar = f"\n{'='*80}\n"

    current_app.logger.debug(f"{bar}Sending {method} request to {endpoint}:")
    if "data" in kwargs:
        data = kwargs["data"]
        if isinstance(data, dict):
            current_app.logger.debug(f"data = {json.dumps(data, indent=2)}")
            kwargs["data"] = json.dumps(data)

    response = methods_dict[method](endpoint, **kwargs)

    headers_sent = dict(response.request.headers)
    current_app.logger.debug(f"Headers sent: {json.dumps(headers_sent, indent=2)}")
    try:
        response_str = json.dumps(response.json(), indent=2)
    except json.decoder.JSONDecodeError:
        response_str = response.text

    if not response.ok:
        current_app.logger.error(f"{response.status_code} Error: {response_str}\n\n")
    else:
        debug_id = f"debug_id = {response.headers.get('PayPal-Debug-Id', None)}"
        current_app.logger.debug(
            f"({debug_id}) {response.status_code} Response: {response_str}{bar}"
        )

    return response


from functools import cache


@cache
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
    try:
        current_app.logger.debug(
            f'*****\n\nAccess token debug_id = {response.headers["PayPal-Debug-Id"]}\n\n*****'
        )
    except:
        pass
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
        response = log_and_request("POST", endpoint, headers=headers, data=data)

    response_dict = response.json()
    return response_dict["client_token"]
    # return response_dict["id_token"] if customer_id else response_dict["client_token"]


def random_decimal_string(length):
    """Return a decimal string of the given length chosen uniformly at random."""
    random_int = random.randrange(10 ** length, 10 ** (length + 1))
    return f"{random_int}"


def money_amount(amount=0, currency_code=None):
    if currency_code is None:
        currency_code = "USD"
    return {"currency_code": currency_code, "amount": amount}
