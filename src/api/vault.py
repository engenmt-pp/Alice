import json
import requests

from flask import Blueprint, current_app, jsonify, request
from .utils import (
    build_endpoint,
    format_request_and_response,
)
from .identity import build_headers
from .orders import default_shipping_address

bp = Blueprint("vault", __name__, url_prefix="/vault")


class Vault:
    def __init__(self, **kwargs):
        self.auth_header = kwargs.get("authHeader", None)
        self.payment_source_type = kwargs.get(
            "payment-source",
            "card",  # If 'payment-source' is undefined, it must be a card transaction!
        )

        self.vault_level = kwargs.get("vault-level")
        self.vault_id = kwargs.get("vault-id")
        self.customer_id = kwargs.get("customer-id")

        self.shipping_preference = kwargs.get("shipping-preference", "NO_SHIPPING")
        self.include_shipping_address = kwargs.get("include-shipping-address", False)

        try:
            self.include_auth_assertion = bool(kwargs["include-auth-assertion"])
        except KeyError:
            self.include_auth_assertion = self.vault_level == "MERCHANT"
        self.include_request_id = (
            True  # This is required to specify `experience_context`.
        )
        if "setup-token-id" in kwargs:
            self.setup_token = kwargs["setup-token-id"]
        if "payment-token-id" in kwargs:
            self.payment_token = kwargs["payment-token-id"]
        if "customer-id" in kwargs:
            self.customer_id = kwargs["customer-id"]

        self.formatted = dict()

    def build_headers(self):
        headers = build_headers(
            auth_header=self.auth_header,
            include_auth_assertion=self.include_auth_assertion,
            include_request_id=self.include_request_id,
            return_formatted=True,
        )
        if "formatted" in headers:
            self.formatted |= headers["formatted"]
            del headers["formatted"]

        self.auth_header = headers["Authorization"]
        return headers

    def build_payment_source(self, for_token):
        match for_token:
            case "setup":
                experience_context = {
                    "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                    "return_url": "http://go/alice/returnUrl",
                    "cancel_url": "http://go/alice/cancelUrl",
                }
                if self.shipping_preference:
                    experience_context["shipping_preference"] = self.shipping_preference

                payment_source_body = {
                    "description": "A description of a PayPal payment source.",
                    "permit_multiple_payment_tokens": True,
                    "usage_pattern": "IMMEDIATE",
                    "customer_type": "CONSUMER",
                    "usage_type": self.vault_level,
                    "experience_context": experience_context,
                }
                if self.include_shipping_address:
                    payment_source_body["shipping"] = default_shipping_address()

                payment_source = {self.payment_source_type: payment_source_body}

            case "payment":
                payment_source = {
                    "token": {
                        "id": self.setup_token,
                        "type": "SETUP_TOKEN",
                    }
                }
            case _:
                raise ValueError(f"{for_token=}")
        return payment_source

    def create_setup_token(self):
        endpoint = build_endpoint("/v3/vault/setup-tokens")
        headers = self.build_headers()

        data = {
            "payment_source": self.build_payment_source(for_token="setup"),
        }
        response = requests.post(
            endpoint,
            headers=headers,
            json=data,
        )
        self.formatted["create-setup-token"] = format_request_and_response(response)
        response_dict = {
            "formatted": self.formatted,
            "authHeader": self.auth_header,
        }

        try:
            setup_token_id = response.json()["id"]
        except Exception as exc:
            current_app.logger.error(
                f"Encountered exception unpacking setup token: {exc}"
            )
            return response_dict

        response_dict["setupTokenId"] = setup_token_id
        return response_dict

    def create_payment_token(self):
        endpoint = build_endpoint("/v3/vault/payment-tokens")
        headers = self.build_headers()

        data = {
            "payment_source": self.build_payment_source(for_token="payment"),
        }
        response = requests.post(
            endpoint,
            headers=headers,
            json=data,
        )
        self.formatted["create-payment-token"] = format_request_and_response(response)
        response_dict = {
            "formatted": self.formatted,
            "authHeader": self.auth_header,
        }

        try:
            payment_token_id = response.json()["id"]
        except Exception as exc:
            current_app.logger.error(
                f"Encountered exception unpacking setup token: {exc}"
            )
            return response_dict

        response_dict["paymentTokenId"] = payment_token_id
        return response_dict

    def get_payment_token_status(self):
        endpoint = build_endpoint(f"/v3/vault/payment-tokens/{self.payment_token}")
        headers = self.build_headers()

        response = requests.get(endpoint, headers=headers)
        self.formatted["payment-token-status"] = format_request_and_response(response)
        response_dict = {
            "formatted": self.formatted,
            "authHeader": self.auth_header,
        }

        return response_dict

    def get_payment_tokens(self):
        endpoint = build_endpoint(
            f"/v3/vault/payment-tokens", query={"customer_id": self.customer_id}
        )
        headers = self.build_headers()

        response = requests.get(endpoint, headers=headers)
        self.formatted["list-payment-tokens"] = format_request_and_response(response)
        response_dict = {
            "formatted": self.formatted,
            "authHeader": self.auth_header,
        }

        return response_dict


@bp.route("/setup-tokens", methods=("POST",))
def create_setup_token():
    data = request.get_json()

    data_filtered = {key: value for key, value in data.items() if value}

    current_app.logger.debug(
        f"Creating a vault setup token with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    vault = Vault(**data)
    resp = vault.create_setup_token()

    current_app.logger.debug(
        f"Create setup token response: {json.dumps(resp, indent=2)}"
    )
    return jsonify(resp)


@bp.route("/setup-tokens/<setup_token_id>", methods=("POST",))
def create_payment_token(setup_token_id):
    data = request.get_json()
    data["setup-token-id"] = setup_token_id

    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.debug(
        f"Creating a vault payment token with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    vault = Vault(**data)
    resp = vault.create_payment_token()

    current_app.logger.debug(
        f"Create setup token response: {json.dumps(resp, indent=2)}"
    )
    return jsonify(resp)


@bp.route("/payment-tokens/<payment_token_id>", methods=("POST",))
def payment_token_status(payment_token_id):
    data = request.get_json()
    data["payment-token-id"] = payment_token_id
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.info(
        f"Getting the status of payment token with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    vault = Vault(**data)
    resp = vault.get_payment_token_status()

    current_app.logger.debug(
        f"Payment token status response: {json.dumps(resp, indent=2)}"
    )
    return jsonify(resp)


@bp.route("/customers/<customer_id>", methods=("POST",))
def get_vault_tokens(customer_id):
    data = request.get_json()
    data["customer-id"] = customer_id
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.info(
        f"Getting the payment tokens of a customer with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    vault = Vault(**data)
    resp = vault.get_payment_tokens()

    current_app.logger.debug(
        f"Payment token list response: {json.dumps(resp, indent=2)}"
    )
    return jsonify(resp)
