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
        if isinstance(data, (dict, list)):
            current_app.logger.debug(f"data = {json.dumps(data, indent=2)}")
            kwargs["data"] = json.dumps(data)

    response = methods_dict[method](endpoint, **kwargs)

    headers_sent = dict(response.request.headers)
    try:
        current_app.logger.debug(f"Headers sent: {json.dumps(headers_sent, indent=2)}")
    except TypeError:
        headers_sent_copy = dict(headers_sent)
        auth_assertion_str = str(headers_sent["PayPal-Auth-Assertion"], "utf-8")
        headers_sent_copy["PayPal-Auth-Assertion"] = f"b'{auth_assertion_str}'"
        current_app.logger.debug(
            f"Headers* sent: {json.dumps(headers_sent_copy, indent=2)}"
        )

    try:
        response_str = json.dumps(response.json(), indent=2)
    except json.decoder.JSONDecodeError:
        response_str = response.text

    if not response.ok:
        current_app.logger.error(f"{response.status_code} Error: {response_str}\n\n")
    else:
        debug_id = response.headers.get("PayPal-Debug-Id")
        current_app.logger.debug(
            f"({debug_id=}) {response.status_code} Response: {response_str}{bar}"
        )

    return response


from functools import cache


@cache
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
    try:
        current_app.logger.debug(
            f'*****\n\nAccess token debug_id = {response.headers["PayPal-Debug-Id"]}\n\n*****'
        )
    except:
        pass
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


def build_headers(
    client_id=None,
    secret=None,
    bn_code=None,
    include_bn_code=True,
    include_auth_assertion=False,
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

    if include_bn_code:
        bn_code = bn_code or current_app.config["PARTNER_BN_CODE"]
        headers["PayPal-Partner-Attribution-Id"] = bn_code

    if include_auth_assertion:
        auth_assertion = build_auth_assertion()
        headers["PayPal-Auth-Assertion"] = auth_assertion

    return headers


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


def format_request(request):
    headers_sent_whitelist = [
        "Authorization",
        "Content-Type",
        "PayPal-Auth-Assertion",
        "PayPal-Partner-Attribution-Id",
        "PayPal-Request-Id",
        "Prefer",
    ]
    headers_sent = {
        key: value
        for key, value in request.headers.items()
        if key in headers_sent_whitelist
    }
    try:
        headers_sent_str = json.dumps(headers_sent, indent=2)
    except TypeError:
        headers_sent_copy = dict(headers_sent)
        auth_assertion_str = str(headers_sent["PayPal-Auth-Assertion"], "utf-8")
        headers_sent_copy["PayPal-Auth-Assertion"] = f"b'{auth_assertion_str}'"
        headers_sent_str = json.dumps(headers_sent_copy, indent=2)

    body_sent = request.body
    if body_sent is not None:
        try:
            body_sent = json.loads(body_sent)
        except (json.decoder.JSONDecodeError, TypeError) as exc:
            current_app.logger.error(
                f"Exception occurred during json.loads('{body_sent}'): ({type(exc)}) {exc}"
            )

    method = request.method
    url = request.url
    return "\n".join(
        [
            f"Sending {method} request to {url}:",
            f"Headers sent: {headers_sent_str}",
            f"Body sent: {json.dumps(body_sent, indent=2)}",
        ]
    )


def format_response(response):
    headers_received_whitelist = [
        "Content-Type",
        "Date",
        "Paypal-Debug-Id",
    ]
    headers_received = {
        key: value
        for key, value in response.headers.items()
        if key in headers_received_whitelist
    }
    try:
        body_received = response.json()
    except json.decoder.JSONDecodeError:
        body_received = response.text

    response_code = response.status_code
    debug_id = headers_received.get("Paypal-Debug-Id")
    return "\n".join(
        [
            f"Response:",
            f"Status: {response_code}",
            f"PayPal Debug ID: {debug_id}",
            f"Headers received: {json.dumps(headers_received,indent=2)}",
            f"Body received: {json.dumps(body_received,indent=2)}",
        ]
    )


def format_request_and_response(response):
    """Format an HTTP request and response for output."""
    formatted_request = format_request(response.request)
    formatted_response = format_response(response)
    return "\n\n".join([formatted_request, formatted_response])


def random_decimal_string(length):
    """Return a decimal string of the given length chosen uniformly at random."""
    random_int = random.randrange(10**length, 10 ** (length + 1))
    return f"{random_int}"


def build_src_val(client_id, merchant_id, intent, additional_query):
    base = "https://www.paypal.com/sdk/js"
    query = {
        "client-id": client_id,
        "merchant-id": merchant_id,
        "intent": intent.lower(),
        "currency": "USD",
    }
    if additional_query:
        query |= additional_query
    return f"{base}?{urlencode(query, safe='/,')}"


def build_script_tag(
    client_id,
    merchant_id,
    intent,
    bn_code,
    additional_query,
    client_token=None,
):
    src_val = build_src_val(client_id, merchant_id, intent, additional_query)
    attributes = [
        f"id='paypal-js-sdk'",
        f"src='{src_val}'",
        f"data-partner-attribution-id='{bn_code}'",
    ]
    if client_token is not None:
        attributes.append(f"data-client-token='{client_token}'")
    return " ".join(["<script", *attributes, "></script>"])
