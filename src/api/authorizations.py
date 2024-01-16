import json
import requests

from flask import Blueprint, request, current_app, jsonify

from .identity import build_headers
from .utils import build_endpoint, format_request_and_response


bp = Blueprint("authorizations", __name__, url_prefix="/authorizations")


class Authorization:
    def __init__(self, **kwargs):
        self.formatted = dict()

        self._set_partner_config(kwargs)
        self.auth_header = kwargs.get("auth-header") or None
        self.include_request_id = True

        self.auth_id = kwargs["auth-id"]

        self.include_auth_assertion = bool(kwargs["include-auth-assertion"])

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
        """Get the details of the authorization using the GET /v2/payments/authorizations/{auth_id} endpoint."""
        try:
            headers = self.build_headers()
        except KeyError as exc:
            current_app.logger.error(f"KeyError encountered building headers: {exc}")
            return {"formatted": self.formatted}

        endpoint = build_endpoint(f"/v2/payments/authorizations/{self.auth_id}")
        response = requests.get(endpoint, headers=headers)

        self.formatted["get-auth"] = format_request_and_response(response)

        return_val = {
            "formatted": self.formatted,
            "authHeader": self.auth_header,
        }
        return return_val


@bp.route("/<auth_id>", methods=("POST",))
def get_authorization_details(auth_id):
    """GET the authorization with the given ID.

    Wrapper for Authorization.get_details.
    """
    data = request.get_json()
    data["auth-id"] = auth_id
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.info(
        f"Refunding an order with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    authorization = Authorization(**data)
    resp = authorization.get_details()

    return jsonify(resp)
