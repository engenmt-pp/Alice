import json
import requests

from flask import Blueprint, request, current_app, jsonify

from .identity import build_headers
from .utils import build_endpoint, format_request_and_response


bp = Blueprint("partner", __name__, url_prefix="/partner")


def extract_action_url(links):
    for link in links:
        match link["rel"]:
            case "action_url":
                return link["href"]
    raise Exception("No action URL found!")


class Referral:
    def __init__(self, **kwargs):
        self.auth_header = kwargs.get("auth-header")

        self.referral_token = kwargs.get("referral-token")

        self.tracking_id = kwargs.get("tracking-id")
        self.partner_id = kwargs.get("partnerId")
        self.merchant_id = kwargs.get("merchantId")

        self.product = kwargs.get("product")
        self.vault_level = kwargs.get("vault-level")
        self.tracking_id = kwargs.get("tracking-id")
        self.country_code = kwargs.get("country-code")
        self.email = kwargs.get("email")

        self.partner_logo_url = kwargs.get("partner-logo-url")
        self.partner_return_url = kwargs.get("partner-return-url")

        self.include_legal_consents = kwargs.get("include-legal-consents")

        self.features = [
            value for option, value in kwargs.items() if option.startswith("feature-")
        ]

        self.formatted = dict()

    def build_headers(self):
        """Wrapper for .utils.build_headers."""
        client_id = current_app.config["PARTNER_CLIENT_ID"]
        secret = current_app.config["PARTNER_SECRET"]
        bn_code = current_app.config["PARTNER_BN_CODE"]
        headers = build_headers(
            client_id=client_id,
            secret=secret,
            bn_code=bn_code,
            auth_header=self.auth_header,
        )

        self.formatted |= headers.pop("formatted")

        self.auth_header = headers["Authorization"]
        return headers

    def build_features(self):
        features = self.features
        if self.vault_level == "MERCHANT":
            additional_features = ["VAULT", "BILLING_AGREEMENT"]
            for feature in additional_features:
                if feature not in features:
                    features.append(feature)
        return features

    def build_products(self):
        products = [self.product]
        if self.vault_level == "MERCHANT":
            products.append("ADVANCED_VAULTING")
        return products

    def build_capabilities(self):
        capabilities = []
        if self.vault_level == "MERCHANT":
            capabilities.append("PAYPAL_WALLET_VAULTING_ADVANCED")
        return capabilities

    def build_partner_config_override(self):
        partner_config_override = dict()

        if self.partner_logo_url:
            partner_config_override["partner_logo_url"] = self.partner_logo_url

        if self.partner_return_url:
            partner_config_override |= {
                "return_url": self.partner_return_url,
                "return_url_description": "A description of the return URL",
            }

    def build_operations(self):
        features = self.build_features()
        operations = [
            {
                "operation": "API_INTEGRATION",
                "api_integration_preference": {
                    "rest_api_integration": {
                        "integration_method": "PAYPAL",
                        "integration_type": "THIRD_PARTY",
                        "third_party_details": {"features": features},
                    }
                },
            }
        ]
        return operations

    def build_legal_consents(self):
        legal_consents = []
        if self.include_legal_consents:
            legal_consents.append(
                {
                    "type": "SHARE_DATA_CONSENT",
                    "granted": True,
                }
            )
        return legal_consents

    def build_business_entity(self):
        business_entity = dict()
        if self.country_code:
            business_entity["addresses"] = [
                {
                    "country_code": self.country_code,
                    "type": "WORK",
                }
            ]
        return business_entity

    def create(self):
        endpoint = build_endpoint("/v2/customer/partner-referrals")
        try:
            headers = self.build_headers()
        except KeyError:
            return {"formatted": self.formatted}

        operations = self.build_operations()
        products = self.build_products()
        data = {"operations": operations, "products": products}

        capabilities = self.build_capabilities()
        if capabilities:
            data["capabilities"] = capabilities

        partner_config_override = self.build_partner_config_override()
        if partner_config_override:
            data["partner_config_override"] = partner_config_override

        capabilities = self.build_capabilities()
        if capabilities:
            data["capabilities"] = capabilities

        legal_consents = self.build_legal_consents()
        if legal_consents:
            data["legal_consents"] = legal_consents

        business_entity = self.build_business_entity()
        if business_entity:
            data["business_entity"] = business_entity

        if self.email:
            data["email"] = self.email
        if self.tracking_id:
            data["tracking_id"] = self.tracking_id

        response = requests.post(
            endpoint,
            headers=headers,
            json=data,
        )
        self.formatted["create-referral"] = format_request_and_response(response)
        return_val = {
            "formatted": self.formatted,
            "authHeader": self.auth_header,
        }
        try:
            links = response.json()["links"]
            action_url = extract_action_url(links)
        except Exception as exc:
            current_app.logger.error(
                f"Encountered exception unpacking action URL: {exc}"
            )
        else:
            return_val["actionUrl"] = action_url
        finally:
            return return_val

    def get_merchant_id(self):
        """Return a merchant's ID given the tracking ID used during onboarding with the /v1/customer/partners API.

        Docs: https://developer.paypal.com/docs/platforms/seller-onboarding/before-payment/#5-track-seller-onboarding-status
        """
        if self.partner_id is None or self.tracking_id is None:
            raise ValueError

        endpoint = build_endpoint(
            f"/v1/customer/partners/{self.partner_id}/merchant-integrations",
            query={"tracking_id": self.tracking_id},
        )
        try:
            headers = self.build_headers()
        except KeyError:
            return {"formatted": self.formatted}

        resp = requests.get(endpoint, headers=headers)
        self.formatted["get-merchant-id"] = format_request_and_response(resp)

        merchant_id = resp.json()["merchant_id"]
        return merchant_id

    def seller_status(self):
        if self.partner_id is None:
            raise ValueError

        if self.merchant_id is None:
            if self.tracking_id is None:
                raise ValueError
            try:
                self.merchant_id = self.get_merchant_id()
            except KeyError as exc:
                current_app.logger.error(
                    f"Encountered error getting merchant ID: {exc}"
                )
                return {"formatted": self.formatted}

        endpoint = build_endpoint(
            f"/v1/customer/partners/{self.partner_id}/merchant-integrations/{self.merchant_id}"
        )
        try:
            headers = self.build_headers()
        except KeyError:
            return {"formatted": self.formatted}

        response = requests.get(endpoint, headers=headers)
        self.formatted["seller-status"] = format_request_and_response(response)

        return {"formatted": self.formatted}

    def referral_status(self):
        endpoint = build_endpoint(
            f"/v2/customer/partner-referrals/{self.referral_token}"
        )
        try:
            headers = self.build_headers()
        except KeyError:
            return {"formatted": self.formatted}

        response = requests.get(endpoint, headers=headers)
        self.formatted["referral-status"] = format_request_and_response(response)

        return {"formatted": self.formatted}


@bp.route("/referrals", methods=("POST",))
def create_referral():
    data = request.get_json()
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.debug(
        f"Creating partner referral with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    referral = Referral(**data)
    resp = referral.create()

    current_app.logger.debug(f"Create referral response: {json.dumps(resp, indent=2)}")
    return jsonify(resp)


@bp.route("/referrals/<referral_token>", methods=("POST",))
def get_referral_status(referral_token):
    data = request.get_json()
    data["referral-token"] = referral_token
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.debug(
        f"Getting referral status with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    referral = Referral(**data)
    resp = referral.referral_status()

    current_app.logger.debug(
        f"Get referral status response: {json.dumps(resp, indent=2)}"
    )
    return jsonify(resp)


@bp.route("/sellers/<merchant_id>", methods=("POST",))
def get_seller_status(merchant_id):
    data = request.get_json()
    data["merchant-id"] = merchant_id
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.debug(
        f"Getting seller status with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    referral = Referral(**data)
    resp = referral.seller_status()

    current_app.logger.debug(
        f"Get seller status response: {json.dumps(resp, indent=2)}"
    )
    return jsonify(resp)


@bp.route("/sellers", methods=("POST",))
def get_seller_status_by_tracking_id():
    data = request.get_json()
    data.update(request.args)
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.debug(
        f"Getting seller status with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    referral = Referral(**data)
    resp = referral.seller_status()

    current_app.logger.debug(
        f"Get seller status response: {json.dumps(resp, indent=2)}"
    )
    return jsonify(resp)
