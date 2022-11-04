import json
from datetime import datetime, timedelta, timezone
from flask import Blueprint, current_app, jsonify, request

from .utils import build_endpoint, build_headers, log_and_request, random_decimal_string


bp = Blueprint("charities", __name__, url_prefix="/charities")


@bp.route("/")
def get_charities():
    query = {
        "name": "Nicholas Orthodox",
        "total_required": False,
        "page_size": 1,
        "page": 1,
    }
    query = {
        "ein": "813208709RR0001",
    }
    endpoint = build_endpoint("/v1/customer/charities", query=query)
    headers = build_headers()

    resp = log_and_request("GET", endpoint, headers=headers)
    return resp
