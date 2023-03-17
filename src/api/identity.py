import requests

from flask import Blueprint
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
