from flask import Blueprint, current_app, jsonify, request

import json

from .utils import (
    build_endpoint,
    build_headers,
    log_and_request,
    format_request_and_response,
)

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
    current_app.logger.error(f"form_options = {json.dumps(form_options, indent=2)}")

    product = form_options.get("product")
    tracking_id = form_options.get("tracking-id")
    return_url = "http://localhost:5000"
    features = [
        value for option, value in form_options.items() if option.startswith("feature-")
    ]
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
        "products": [product],
        "legal_consents": [{"type": "SHARE_DATA_CONSENT", "granted": True}],
        "partner_config_override": {
            "return_url": return_url,
            "return_url_description": "A description of the return URL.",
        },
    }
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
    referral_url = extract_referral_url(response.json()["links"])
    response_dict = {"formatted": formatted, "referralUrl": referral_url}
    return response_dict
