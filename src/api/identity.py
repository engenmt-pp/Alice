import requests

from flask import Blueprint, current_app
from .utils import (
    build_endpoint,
    build_headers,
    log_and_request,
    format_request_and_response,
)


bp = Blueprint("identity", __name__, url_prefix="/identity")


def generate_client_token(customer_id=None, return_formatted=False):
    endpoint = build_endpoint("/v1/identity/generate-token")
    headers = build_headers(return_formatted=return_formatted)
    if return_formatted:
        formatted = headers["formatted"]
        del headers["formatted"]

    if customer_id is None:
        response = requests.post(endpoint, headers=headers)
    else:
        data = {"customer_id": customer_id}
        response = log_and_request("POST", endpoint, headers=headers, data=data)

    client_token = response.json()["client_token"]

    if return_formatted:
        formatted["client-token"] = format_request_and_response(response)
        return {"client_token": client_token, "formatted": formatted}

    return client_token


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
