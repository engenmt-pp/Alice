from flask import Blueprint, current_app
from .utils import build_endpoint, build_headers, log_and_request


bp = Blueprint("referrals", __name__, url_prefix="/referrals")


def generate_onboarding_urls(
    tracking_id, version="v2", return_url="http://localhost:5000/"
):
    """Return the onboarding and referral URLs generated with the partner referrals API."""
    if version == "v1":
        response = create_partner_referral_v1(tracking_id, return_url=return_url)
    else:
        response = create_partner_referral_v2(tracking_id, return_url=return_url)

    onboarding_url = None
    referral_url = None
    for link in response["links"]:
        match link["rel"]:
            case "action_url":
                onboarding_url = link["href"]
            case "self":
                referral_url = link["href"]
            case other:
                raise Exception(f"Unknown onboarding URL relation: {other}")

    if onboarding_url is None or referral_url is None:
        raise Exception("Not all onboarding URLs found!")

    return onboarding_url, referral_url


def create_partner_referral_v1(tracking_id, return_url):
    """Return a partner-referral URL requested from the /v1/customer/partner-referrals API.

    Docs: https://developer.paypal.com/docs/api/partner-referrals/v1/#partner-referrals_create
    """
    endpoint = build_endpoint("/v1/customer/partner-referrals")
    headers = build_headers()

    partner_id = current_app.config["PARTNER_ID"]
    partner_client_id = current_app.config["PARTNER_CLIENT_ID"]

    data = {
        "customer_data": {
            "customer_type": "MERCHANT",
            "preferred_language_code": "en_US",
            "primary_currency_code": "USD",
            "partner_specific_identifiers": [
                {"type": "TRACKING_ID", "value": tracking_id}
            ],
        },
        "requested_capabilities": [
            {
                "capability": "API_INTEGRATION",
                "api_integration_preference": {
                    "partner_id": partner_id,
                    "rest_api_integration": {
                        "integration_method": "PAYPAL",
                        "integration_type": "THIRD_PARTY",
                    },
                    "rest_third_party_details": {
                        "partner_client_id": partner_client_id,
                        "feature_list": ["PAYMENT", "REFUND", "READ_SELLER_DISPUTE"],
                    },
                },
            }
        ],
        "web_experience_preference": {
            "partner_logo_url": "https://www.paypalobjects.com/digitalassets/c/website/marketing/na/us/logo-center/Badge_1.png",
            "return_url": return_url,
            "action_renewal_url": "www.url.com",
        },
        "collected_consents": [{"type": "SHARE_DATA_CONSENT", "granted": True}],
        "products": ["EXPRESS_CHECKOUT"],
    }

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    return response.json()


def create_partner_referral_v2(tracking_id, return_url):
    """Call the /v2/customer/partner-referrals API to generate a sign-up link.

    Docs: https://developer.paypal.com/docs/api/partner-referrals/v2/#partner-referrals_create
    """
    endpoint = build_endpoint("/v2/customer/partner-referrals")
    headers = build_headers()

    ACDC = False
    product = "PPCP" if ACDC else "EXPRESS_CHECKOUT"

    data = {
        "tracking_id": tracking_id,
        "operations": [
            {
                "operation": "API_INTEGRATION",
                "api_integration_preference": {
                    "rest_api_integration": {
                        "integration_method": "PAYPAL",
                        "integration_type": "THIRD_PARTY",
                        "third_party_details": {
                            "features": [
                                "PAYMENT",
                                "REFUND",
                                "PARTNER_FEE",
                                "FUTURE_PAYMENT",
                                # "DELAY_FUNDS_DISBURSEMENT",
                                # "VAULT",
                                # "ADVANCED_TRANSACTIONS_SEARCH",
                            ]
                        },
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

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    response_dict = response.json()
    return response_dict


def get_merchant_id(tracking_id):
    """Return a merchant's ID given the tracking ID used during onboarding with the /v1/customer/partners API.

    Docs: https://developer.paypal.com/docs/platforms/seller-onboarding/before-payment/#5-track-seller-onboarding-status
    """
    partner_id = current_app.config["PARTNER_ID"]

    endpoint = build_endpoint(
        f"/v1/customer/partners/{partner_id}/merchant-integrations",
        query={"tracking_id": tracking_id},
    )
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict["merchant_id"]


def get_onboarding_status(merchant_id):
    """Get the status of a merchant's onboarding with the /v1/customer/partners API.

    Docs: https://developer.paypal.com/docs/platforms/seller-onboarding/before-payment/#5-track-seller-onboarding-status
    """
    partner_id = current_app.config["PARTNER_ID"]

    endpoint = build_endpoint(
        f"/v1/customer/partners/{partner_id}/merchant-integrations/{merchant_id}"
    )
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict


def get_partner_referral_id(referral_url):
    return referral_url.split("/")[-1]


def get_referral_status(partner_referral_id):
    """Get the status of a partner referral with the /v2/customer/partner-referrals API.

    Docs: https://developer.paypal.com/api/partner-referrals/v2/#partner-referrals_read
    """
    endpoint = build_endpoint(f"/v2/customer/partner-referrals/{partner_referral_id}")
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict
