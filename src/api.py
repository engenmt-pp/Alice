import base64
import json
import requests
import secrets

from datetime import datetime, timedelta, timezone
from flask import Blueprint, current_app, request, jsonify
from urllib.parse import urlencode

bp = Blueprint("api", __name__, url_prefix="/api")

REPORTS_DIR = "/ppreports/outgoing"
CUSTOMER_ID = "customer_1236"


def build_endpoint(route, query=None):
    """Build the appropriate API endpoint given the suffix/route."""
    endpoint_prefix = current_app.config["ENDPOINT_PREFIX"]
    endpoint = f"{endpoint_prefix}{route}"
    if query is None:
        return endpoint

    query_string = urlencode(query)
    return f"{endpoint}?{query_string}"


def log_and_request(method, endpoint, **kwargs):
    """Log the HTTP request, make the request, and return the response."""
    methods_dict = {
        "GET": requests.get,
        "PATCH": requests.patch,
        "POST": requests.post,
    }
    if method not in methods_dict:
        raise Exception(f"HTTP request method '{method}' not recognized!")

    try:
        kwargs_str = json.dumps(kwargs, indent=2)
    except TypeError:
        kwargs_str = str(kwargs)
    
    current_app.logger.debug(f"\nSending {method} request to {endpoint}:\n{kwargs_str}")

    try:
        kwargs['data'] = json.dumps(kwargs['data'])
    except KeyError:
        pass

    response = methods_dict[method](endpoint, **kwargs)
    try:
        response_str = json.dumps(response.json(), indent=2)
    except json.decoder.JSONDecodeError:
        response_str = response.text
    
    if not response.ok:
        current_app.logger.error(f"Error: {response_str}\n\n")
    else:
        current_app.logger.debug(f"Response: {response_str}\n\n")

    return response


def request_access_token(client_id, secret):
    """Call the /v1/oauth2/token API to request an access token.

    Docs: https://developer.paypal.com/docs/api/reference/get-an-access-token/
    """
    endpoint = build_endpoint("/v1/oauth2/token")
    headers = {"Content-Type": "application/json", "Accept-Language": "en_US"}

    data = {"grant_type": "client_credentials", "ignoreCache": True}

    response = requests.post(endpoint, headers=headers, data=data, auth=(client_id, secret))
    response_dict = response.json()

    try:
        return response_dict["access_token"]
    except KeyError as exc:
        current_app.logger.error(f"Encountered a KeyError: {exc}")
        current_app.logger.error(
            f"response_dict = {json.dumps(response_dict, indent=2)}"
        )
        raise exc


def build_headers(client_id=None, secret=None, include_bn_code=False):
    """Build commonly used headers using a new PayPal access token."""
    if client_id is None:
        client_id = current_app.config["PARTNER_CLIENT_ID"]
    if secret is None:
        secret = current_app.config["PARTNER_SECRET"]

    access_token = request_access_token(client_id, secret)
    headers = {
        "Accept": "application/json", 
        "Accept-Language": "en_US",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    if include_bn_code:
        headers["PayPal-Partner-Attribution-Id"] = current_app.config["PARTNER_BN_CODE"]
    
    return headers


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
                                "VAULT"
                                "ADVANCED_TRANSACTIONS_SEARCH",
                            ]
                        },
                    }
                },
            }
        ],
        "products": ["PPCP"],
        "legal_consents": [
            {
                "type": "SHARE_DATA_CONSENT", 
                "granted": True
            }
        ],
        "partner_config_override": {"return_url": return_url},
    }

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    response_dict = response.json()
    return response_dict


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
def create_order(include_platform_fees = True):
    """Call the /v2/checkout/orders API to create an order.

    Requires `price` and `payee_id` fields in the request body.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")
    headers = build_headers(include_bn_code=True)

    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "custom_id": "Up to 127 characters can go here!",
                "payee": {"merchant_id": request.json["payee_id"]},
                "amount": {
                    "currency_code": "USD",
                    "value": request.json["price"],
                },
                "soft_descriptor": "1234567890111213141516",
            }
        ],
        "application_context": {
            "return_url": "http://localhost:5000/",
            "cancel_url": "http://localhost:5000/",
            "shipping_preference": "GET_FROM_FILE"
        },
    }

    if include_platform_fees:
        data['purchase_units'][0]["payment_instruction"] = {
            "disbursement_mode": "INSTANT",
            'platform_fees': [
                {
                    "amount": {
                        "currency_code": "USD", 
                        "value": "1.00"
                    }
                }
            ]
        }
    
    if request.json.get('include_shipping', False):
        data['purchase_units'][0]['shipping'] = {
            "options": [
                {
                    "id": "shipping-default",
                    "label": "A default shipping option",
                    "selected": True,
                    "amount": {
                        "currency_code": "USD",
                        "value": "9.99",
                    },
                }
            ]
        }
    
    response = log_and_request("POST", endpoint, headers=headers, data=data)
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/create-order-vault", methods=("POST",))
def create_order_vault():
    """Call the /v2/checkout/orders API to create an order.

    Requires `price` and `payee_merchant_id` fields in the request body.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")
    headers = build_headers(include_bn_code = True)
    headers["PayPal-Request-Id"] = secrets.token_hex(10)

    data = {
        "intent": "CAPTURE",
        "payment_source": {
            "paypal": {
                "attributes": {
                    "customer": {"id": request.json['customer_id']},
                    "vault": {
                        "confirm_payment_token": "ON_ORDER_COMPLETION",
                        "usage_type": "PLATFORM", # For Channel-Initiated Billing (CIB) Billing Agreement
                        # "usage_type": "MERCHANT", # For Merchant-Initiated Billing (MIB) Billing Agreement
                        "customer_type": "CONSUMER"
                    }
                }
            }
        },
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
        "application_context": {
            "return_url": "http://localhost:5000/",
            "cancel_url": "http://localhost:5000/",
            "shipping_preference": "GET_FROM_FILE"
        },
    }

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/create-order-auth", methods=("POST",))
def create_order_auth():
    """Call the /v2/checkout/orders API to create an order with intent=AUTHORIZE.

    Requires `price` and `payee_id` fields in the request body.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
    """
    endpoint = build_endpoint("/v2/checkout/orders")
    headers = build_headers(include_bn_code = True)

    data = {
        "intent": "AUTHORIZE",
        "purchase_units": [
            {
                "custom_id": "Up to 127 characters can go here!",
                "payee": {"merchant_id": request.json["payee_id"]},
                "amount": {
                    "currency_code": "USD",
                    "value": request.json["price"],
                },
            }
        ],
        "application_context": {"shipping_preference": "GET_FROM_FILE"},
    }

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/auth-capture/<order_id>", methods=("POST",))
def authorize_and_capture_order(order_id):
    """Authorize and then capture the order."""
    response_dict = authorize_order(order_id)
    auth_id = response_dict['purchase_units'][0]['payments']['authorizations'][0]['id']
    return capture_authorization(auth_id)


def authorize_order(order_id):
    """Authorize the order using the /v2/checkout/orders API.
    
    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_authorize
    """

    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}/authorize")
    headers = build_headers()

    response = log_and_request("POST", endpoint, headers=headers)
    response_dict = response.json()
    return response_dict


def capture_authorization(auth_id, partner_fees = True):
    """Capture the authorization with the given `auth_id` using the /v2/payments/ API.

    Docs: https://developer.paypal.com/docs/api/payments/v2/#authorizations_capture
    """
    endpoint = build_endpoint(f"/v2/payments/authorizations/{auth_id}/capture")
    headers = build_headers()

    if partner_fees:
        data = {
            "payment_instruction": {
                "disbursement_mode": "INSTANT",
                "platform_fees": [
                    {
                        "amount": {
                            "currency_code": "USD", 
                            "value": "1.00"
                        }
                    }
                ]
            }
        }
    else:
        data = {}

    response = log_and_request("POST", endpoint, headers=headers, data=data)
    response_dict = response.json()
    return jsonify(response_dict)


@bp.route("/capture-order/<order_id>", methods=("POST",))
def capture_order(order_id):
    """Call the /v2/checkout/orders API to capture an order.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}/capture")
    headers = build_headers()

    response = log_and_request("POST", endpoint, headers=headers)
    response_dict = response.json()

    return jsonify(response_dict)


@bp.route("/capture-order-vault/<order_id>", methods=("POST",))
def capture_order_vault(order_id):
    """Call the /v2/checkout/orders API to capture an order.

    Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}/capture")
    headers = build_headers()

    response = log_and_request("POST", endpoint, headers=headers)
    response_dict = response.json()

    return jsonify(response_dict)


@bp.route("/determine-shipping", methods=("GET",))
def determine_shipping():
    """Determine new shipping options given a customer's shipping address.

    Notes: This method returns a hard-coded determined shipping option.
        More could happen here, of course.
    """
    return jsonify([
        {
            "id": "shipping-determined",
            "label": "A determined shipping option",
            "selected": True,
            "amount": {
                "value": "4.99",
                "currency_code": "USD",
            },
        }
    ])


@bp.route("/update-shipping/<order_id>", methods=("POST",))
def update_shipping(order_id):
    """Replace the order's shipping option with the /v2/checkout/orders API.

    In sandbox, this occaisionally fails to result in updated shipping options despite a 204 response.
    
    Docs: https://developer.paypal.com/api/orders/v2/#orders_patch
    """
    endpoint = build_endpoint(f"/v2/checkout/orders/{order_id}")
    headers = build_headers()

    data = [
        {
            "op": "replace",
            "path": "/purchase_units/@reference_id=='default'/shipping/options",
            "value": [
                {
                    "id": "shipping-update",
                    "label": "An updated shipping option",
                    "selected": True,
                    "amount": {
                        "value": "9.99",
                        "currency_code": "USD",
                    },
                }
            ],
        }
    ]
    response = log_and_request('PATCH', endpoint, headers=headers, data=data)

    if response.status_code != 204:
        current_app.logger.error(f"Encountered a non-204 response from PATCH: \n{json.dumps(response.json(), indent=2)}")
        raise Exception("Encountered and error in the update_shipping PATCH!")

    return "", 204


def get_order_details(order_id):
    """Get the details of the order with the /v2/checkout/orders API.

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

    response = log_and_request("POST", endpoint, headers=headers, data=verification_dict)
    response_dict = response.json()
    return response_dict


@bp.route("/gen-client-token")
def generate_client_token(customer_id):
    endpoint = build_endpoint("/v1/identity/generate-token")
    headers = build_headers()    

    data = {"customer_id": customer_id}

    response = requests.post(endpoint, headers=headers, data=data)
    response_dict = response.json()
    return response_dict["client_token"]


def list_payment_tokens(customer_id):
    query = {'customer_id': customer_id}
    endpoint = build_endpoint(f"/v2/vault/payment-tokens", query=query)
    headers = build_headers()

    response = log_and_request("GET", endpoint, headers=headers)
    return response
    

def refund_order(capture_id):
    endpoint = build_endpoint(f"/v2/payments/captures/{capture_id}/refund")

    headers = build_headers()
    headers["PayPal-Auth-Assertion"] = build_auth_assertion()

    data = {"note_to_payer": "Apologies for the inconvenience!"}

    response = requests.post(endpoint, headers=headers, data=json.dumps(data))
    response_dict = response.json()
    return response_dict


def get_transactions():
    """Get the transactions from the preceding four weeks.

    This requires the "ADVANCED_TRANSACTIONS_SEARCH" option enabled at onboarding.

    Docs: https://developer.paypal.com/docs/api/transaction-search/v1/
    """
    headers = build_headers()
    headers["PayPal-Auth-Assertion"] = build_auth_assertion()

    end_date = datetime.now(tz=timezone.utc)
    start_date = end_date - timedelta(days=28)
    query = {
        "start_date": start_date.isoformat(timespec="seconds"),
        "end_date": end_date.isoformat(timespec="seconds"),
    }

    endpoint = build_endpoint(f"/v1/reporting/transactions", query)

    response = requests.get(endpoint, headers=headers)
    response_dict = response.json()
    return response_dict
