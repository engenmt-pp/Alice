from flask import Blueprint, current_app, jsonify, request

import json

from .utils import (
    build_endpoint,
    log_and_request,
    format_request_and_response,
)

from .identity import build_headers

bp = Blueprint("referrals_form", __name__, url_prefix="/referrals-form")


def extract_referral_url(links):
    for link in links:
        match link["rel"]:
            case "action_url":
                return link["href"]
    raise Exception("No action URL found!")


@bp.route("/generate", methods=("POST",))
def generate_partner_referral():
    endpoint = build_endpoint("/v2/customer/partner-referrals")
    headers = build_headers(return_formatted=True)
    formatted = headers["formatted"]
    del headers["formatted"]

    form_options = request.get_json()
    current_app.logger.debug(f"form_options = {json.dumps(form_options, indent=2)}")

    features = [
        value for option, value in form_options.items() if option.startswith("feature-")
    ]

    product = form_options.get("product")
    products = [product]
    vault_v3 = form_options.get("vault-v3")
    match vault_v3:
        case "merchant-level":
            features.extend(["VAULT", "BILLING_AGREEMENT"])
            products.append("ADVANCED_VAULTING")
            capabilities = ["PAYPAL_WALLET_VAULTING_ADVANCED"]
        case _:
            capabilities = []

    tracking_id = form_options.get("tracking-id")
    country_code = form_options.get("country-code")
    email = form_options.get("email")

    data = {
        "operations": [
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
        ],
        "products": products,
    }
    if capabilities:
        data["capabilities"] = capabilities

    include_legal_consents = form_options.get("include-legal-consents", "")
    if include_legal_consents:
        data["legal_consents"] = [{"type": "SHARE_DATA_CONSENT", "granted": True}]

    partner_config_override = dict()
    partner_logo_url = form_options.get("partner-logo-url")
    if partner_logo_url:
        partner_config_override["partner_logo_url"] = partner_logo_url
    partner_return_url = form_options.get("partner-return-url")
    if partner_return_url:
        partner_config_override["return_url"] = partner_return_url
        partner_config_override[
            "return_url_description"
        ] = "A description of the return URL"

    if partner_config_override:
        data["partner_config_override"] = partner_config_override

    if country_code:
        data["business_entity"] = (
            {"addresses": [{"country_code": country_code, "type": "WORK"}]},
        )
    if email:
        data["email"] = email

    if tracking_id:
        data["tracking_id"] = tracking_id

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    formatted["generate-referral"] = format_request_and_response(response)
    response_dict = {"formatted": formatted}

    try:
        links = response.json().get("links")
        referral_url = extract_referral_url(links)
    except Exception:
        return response_dict

    response_dict["referralUrl"] = referral_url
    return response_dict
