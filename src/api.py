import base64
import json
import requests

from flask import Blueprint, current_app, request, jsonify

bp = Blueprint("api", __name__, url_prefix="/api")


def build_endpoint(route):
    """Build the appropriate API endpoint given the suffix/route."""
    endpoint_prefix = current_app.config["ENDPOINT_PREFIX"]
    return f"{endpoint_prefix}{route}"


def log_and_request(method, endpoint, **kwargs):
    """Log the HTTP request, make the request, and return the response."""
    methods_dict = {
        "POST": requests.post,
        "GET": requests.get,
    }
    if method not in methods_dict:
        raise Exception(f"HTTP request method '{method}' not recognized!")

    current_app.logger.debug(
        f"\nSending {method} request to {endpoint}:\n{json.dumps(kwargs, indent=2)}"
    )

    response = methods_dict[method](endpoint, **kwargs)
    if not response.ok:
        raise Exception(f"API response is not okay: {response.text}")

    return response


def request_access_token(client_id, secret):
    """Call the /v1/oauth2/token API to request an access token.

    Docs: https://developer.paypal.com/docs/api/reference/get-an-access-token/
    """
    endpoint = build_endpoint("/v1/oauth2/token")
    headers = {"Content-Type": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}

    response = log_and_request(
        "POST", endpoint, headers=headers, data=data, auth=(client_id, secret)
    )
    response_dict = response.json()
    return response_dict["access_token"]


def build_headers(client_id=None, secret=None):
    """Build commonly used headers using a new PayPal access token."""
    if client_id is None:
        client_id = current_app.config["PARTNER_CLIENT_ID"]
    if secret is None:
        secret = current_app.config["PARTNER_SECRET"]
    access_token = request_access_token(client_id, secret)
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }


def build_auth_assertion(client_id=None, merchant_id=None):
    """Build and return the PayPal Auth Assertion.
    Docs: https://developer.paypal.com/docs/api/reference/api-requests/#paypal-auth-assertion
    """
    if client_id is None:
        client_id = current_app.config["PARTNER_CLIENT_ID"]
    if merchant_id is None:
        merchant_id = current_app.config["MERCHANT_ID"]

    header = {"alg": "none"}
    header_b64 = base64.b64encode(json.dumps(header).encode("ascii"))

    payload = {"iss": client_id, "payer_id": merchant_id}
    payload_b64 = base64.b64encode(json.dumps(payload).encode("ascii"))

    signature = b""
    return b".".join([header_b64, payload_b64, signature])


def generate_onboarding_urls(tracking_id, version="v2", return_url="paypal.com"):
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
    """Call the /v1/customer/partner-referrals API to generate a sign-up link.

    Docs: https://developer.paypal.com/docs/api/partner-referrals/v1/#partner-referrals_create
    """
    endpoint = build_endpoint("/v1/customer/partner-referrals")
    headers = build_headers()
    data = {
        "customer_data": {
            "customer_type": "MERCHANT",
            "preferred_language_code": "en_US",
            "primary_currency_code": "USD",
            "partner_specific_identifiers": [
                {
                    "type": "TRACKING_ID",
                    "value": tracking_id
                }
            ]
        },
        "requested_capabilities": [
            {
                "capability": "API_INTEGRATION",
                "api_integration_preference": {
                    "partner_id": current_app.config["PARTNER_ID"],
                    "rest_api_integration": {
                        "integration_method": "PAYPAL",
                        "integration_type": "THIRD_PARTY"
                    },
                    "rest_third_party_details": {
                        "partner_client_id": current_app.config["PARTNER_CLIENT_ID"],
                        "feature_list": [
                            "PAYMENT",
                            "REFUND",
                            "READ_SELLER_DISPUTE"
                        ]
                    }
                }
            }
        ],
        "web_experience_preference": {
            "partner_logo_url": "https://www.paypalobjects.com/digitalassets/c/website/marketing/na/us/logo-center/Badge_1.png",
            "return_url": return_url,
            "action_renewal_url": "www.url.com"
        },
        "collected_consents": [
            {
                "type": "SHARE_DATA_CONSENT",
                "granted": True
            }
        ],
        "products": [
            "EXPRESS_CHECKOUT"
        ]
    }

    response = log_and_request("POST", endpoint, headers=headers, data=json.dumps(data))
    return response.json()


def create_partner_referral_v2(tracking_id, return_url):
    """Call the /v2/customer/partner-referrals API to generate a sign-up link.

    Docs: https://developer.paypal.com/docs/api/partner-referrals/v2/#partner-referrals_create
    """
    endpoint = build_endpoint("/v2/customer/partner-referrals")
    headers = build_headers()
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
                                "DELAY_FUNDS_DISBURSEMENT",
                            ]
                        },
                    }
                },
            }
        ],
        "products": ["PPCP"],
        "legal_consents": [{"type": "SHARE_DATA_CONSENT", "granted": True}],
        "partner_config_override": {"return_url": return_url},
    }

    response = log_and_request("POST", endpoint, headers=headers, data=json.dumps(data))
    return response.json()


def get_merchant_id(tracking_id, partner_id=None):
    """Call the /v1/customer/partners API to get a merchant's merchant_id.

    Docs: https://developer.paypal.com/docs/platforms/seller-onboarding/before-payment/#5-track-seller-onboarding-status
    """
    if partner_id is None:
        partner_id = current_app.config["PARTNER_ID"]

    endpoint = build_endpoint(
        f"/v1/customer/partners/{partner_id}/merchant-integrations?tracking_id={tracking_id}"
    )
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict["merchant_id"]


def get_onboarding_status(merchant_id, partner_id=None):
    """Call the /v1/customer/partners API to get the status of a merchant's onboarding.

    Docs: https://developer.paypal.com/docs/platforms/seller-onboarding/before-payment/#5-track-seller-onboarding-status
    """
    if partner_id is None:
        partner_id = current_app.config["PARTNER_ID"]

    endpoint = build_endpoint(
        f"/v1/customer/partners/{partner_id}/merchant-integrations/{merchant_id}"
    )
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict


def get_partner_referral_id(referral_url):
    return referral_url.split('/')[-1]


def get_referral_status(partner_referral_id):
    """Call the /v2/customer/partner-referrals API to get the status of a referral.

    Docs: https://developer.paypal.com/api/partner-referrals/v2/#partner-referrals_read
    """
    endpoint = build_endpoint(
        f"/v2/customer/partner-referrals/{partner_referral_id}"
    )
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict


@bp.route("/create-order", methods=("POST",))
def create_order():
    """Call the /v2/checkout/orders API to create an order.

    Requires `bn_code`, `price`, and `payee_merchant_id` fields in the request body.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")

    headers = build_headers()
    headers["PayPal-Partner-Attribution-Id"] = request.json["bn_code"]

    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "custom_id": "Up to 127 characters can go here!",
                "payee": {"merchant_id": request.json["payee_id"]},
                "payment_instruction": {"disbursement_mode": "INSTANT"},
                "amount": {
                    "currency_code": "USD",
                    "value": request.json["price"],
                },
            }
        ],
    }

    response = log_and_request("POST", endpoint, headers=headers, data=json.dumps(data))
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/capture-order", methods=("POST",))
def capture_order():
    """Call the /v2/checkout/orders API to capture an order.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{request.json['orderId']}/capture")
    headers = build_headers()

    response = log_and_request("POST", endpoint, headers=headers)
    response_dict = response.json()
    return jsonify(response_dict)


def get_order_details(order_id):
    """Call the /v2/checkout/orders API to get order details.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_get
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}")
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict


def verify_webhook_signature(verification_dict):
    """Verify the signature of the webhook to ensure it is genuine.

    Docs: https://developer.paypal.com/api/webhooks/v1/#verify-webhook-signature_post
    """
    endpoint = build_endpoint("/v1/notifications/verify-webhook-signature")
    headers = build_headers()

    response = log_and_request(
        "POST", endpoint, headers=headers, data=json.dumps(verification_dict)
    )
    response_dict = response.json()
    return response_dict
