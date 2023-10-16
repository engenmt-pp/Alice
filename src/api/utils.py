import json
import random

from flask import current_app
from urllib.parse import urlencode
from shlex import quote


def get_managed_partner_config(model):
    word_map = {
        1: "ONE",
        2: "TWO",
    }
    model = word_map[model]

    partner_config = {
        "id": current_app.config[f"MP_PARTNER_{model}_ID"],
        "client_id": current_app.config[f"MP_PARTNER_{model}_CLIENT_ID"],
        "secret": current_app.config[f"MP_PARTNER_{model}_SECRET"],
        "bn_code": current_app.config[f"MP_PARTNER_{model}_BN_CODE"],
    }

    return partner_config


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
            body_sent_str = str(body_sent)
        else:
            body_sent_str = json.dumps(body_sent, indent=2)
    else:
        body_sent_str = "null"

    method = request.method
    url = request.url
    return "\n".join(
        [
            f"Sending {method} request to {url}:",
            f"Headers sent: {headers_sent_str}",
            f"Body sent: {body_sent_str}",
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
    reason = response.reason
    debug_id = headers_received.get("Paypal-Debug-Id")
    return "\n".join(
        [
            f"Response:",
            f"Status: {response_code} {reason}",
            f"PayPal Debug ID: {debug_id}",
            f"Headers received: {json.dumps(headers_received,indent=2)}",
            f"Body received: {json.dumps(body_received,indent=2)}",
        ]
    )


def format_request_and_response(response):
    """Format an HTTP request and response for output."""
    request = response.request
    formatted_request = format_request(request)
    curl_formatted_request = format_request_as_curl(request)

    formatted_response = format_response(response)
    human_formatted_request = "\n\n".join([formatted_request, formatted_response])
    return {
        "human": human_formatted_request,
        "curl": curl_formatted_request,
    }


def format_request_as_curl(request):
    """Format the HTTP request as a cURL command."""
    method = quote(request.method)
    url = quote(request.url)
    lines = [f"curl -X {method} {url}"]

    for header, value in sorted(request.headers.items()):
        if header == "User-Agent":
            continue
        header = quote(header)
        lines.append(f'-H "{header}: {value}"')

    if request.body:
        try:
            # This will work if the body is of type 'bytes'.
            request_body = request.body.decode("utf-8")
        except AttributeError:
            request_body = request.body
        body = quote(request_body)
        lines.append(f"-d {body}")

    return " \\\n\t".join(lines)


def random_decimal_string(length):
    """Return a decimal string of the given length chosen uniformly at random."""
    random_int = random.randrange(10**length, 10 ** (length + 1))
    return f"{random_int}"
