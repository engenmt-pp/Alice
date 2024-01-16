import json
import requests

from flask import Blueprint, request, current_app, jsonify

from .identity import build_headers
from .utils import build_endpoint, format_request_and_response


bp = Blueprint("captures", __name__, url_prefix="/captures")


class Capture:
    def __init__(self, **kwargs):
        self.formatted = dict()
        self.breakdown = dict()

        self._set_partner_config(kwargs)
        self.auth_header = kwargs.get("auth-header") or None
        self.capture_id = kwargs["capture-id"]
        self.currency_code = kwargs.get("currency-code", "USD")

        self.include_request_id = True

        try:
            self.include_auth_assertion = bool(kwargs["include-auth-assertion"])
        except KeyError:
            self.include_auth_assertion = self.vault_level == "MERCHANT"

    def _set_partner_config(self, kwargs):
        self.partner_id = kwargs.get("partner-id")
        self.client_id = kwargs.get("partner-client-id")
        self.secret = kwargs.get("partner-secret")
        self.bn_code = kwargs.get("partner-bn-code")
        self.merchant_id = kwargs.get("merchant-id")

        if self.client_id == current_app.config["PARTNER_CLIENT_ID"]:
            self.secret = current_app.config["PARTNER_SECRET"]

    def build_headers(self):
        """Wrapper for .utils.build_headers."""
        if self.include_auth_assertion:
            merchant_id = self.merchant_id
        else:
            merchant_id = None

        headers = build_headers(
            client_id=self.client_id,
            secret=self.secret,
            bn_code=self.bn_code,
            auth_header=self.auth_header,
            merchant_id=merchant_id,
            include_request_id=self.include_request_id,
        )
        self.formatted |= headers.pop("formatted")

        self.auth_header = headers["Authorization"]
        return headers

    def get_details(self):
        """Get the details of the capture using the GET /v2/payments/captures/{capture_id} endpoint."""
        try:
            headers = self.build_headers()
        except KeyError as exc:
            current_app.logger.error(f"KeyError encountered building headers: {exc}")
            return {"formatted": self.formatted}

        endpoint = build_endpoint(f"/v2/payments/captures/{self.capture_id}")
        response = requests.get(endpoint, headers=headers)

        self.formatted["get-capture"] = format_request_and_response(response)

        return_val = {
            "formatted": self.formatted,
            "authHeader": self.auth_header,
        }
        return return_val

    def refund(self):
        """Refund the capture using the POST /v2/payments/captures/{capture_id}/refund endpoint."""
        try:
            headers = self.build_headers()
        except KeyError as exc:
            current_app.logger.error(f"KeyError encountered building headers: {exc}")
            return {"formatted": self.formatted}

        endpoint = build_endpoint(f"/v2/payments/captures/{self.capture_id}/refund")
        response = requests.post(endpoint, headers=headers)

        self.formatted["refund-capture"] = format_request_and_response(response)

        return_val = {
            "formatted": self.formatted,
            "authHeader": self.auth_header,
        }
        return return_val


@bp.route("/<capture_id>", methods=("POST",))
def get_capture_details(capture_id):
    """GET the capture with the given ID.

    Wrapper for Captures.get_details.
    """
    data = request.get_json()
    data["capture-id"] = capture_id
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.info(
        f"Refunding an order with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    capture = Capture(**data)
    resp = capture.get_details()

    return jsonify(resp)


@bp.route("/<capture_id>/refund", methods=("POST",))
def refund_capture(capture_id):
    """Refund the capture with the given ID.

    Wrapper for Captures.refund.
    """
    data = request.get_json()
    data["capture-id"] = capture_id
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.info(
        f"Refunding an order with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    capture = Capture(**data)
    resp = capture.refund()

    return jsonify(resp)
