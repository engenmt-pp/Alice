import json
import random

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
        headers_sent_copy["PayPal-Auth-Assertion"] = auth_assertion_str
        headers_sent_str = json.dumps(headers_sent_copy, indent=2)

    body_sent = request.body
    if body_sent is not None:
        try:
            body_sent = json.loads(body_sent)
        except (json.decoder.JSONDecodeError, TypeError) as exc:
            current_app.logger.debug(
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
