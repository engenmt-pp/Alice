import json

from flask import Blueprint, current_app, request
from .utils import build_endpoint, build_headers, log_and_request

bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")


def verify_webhook_signature(verification_dict):
    """Verify the signature of the webhook with the /v1/notifications API.

    Docs: https://developer.paypal.com/api/webhooks/v1/#verify-webhook-signature_post
    """
    endpoint = build_endpoint("/v1/notifications/verify-webhook-signature")
    headers = build_headers()

    response = log_and_request(
        "POST", endpoint, headers=headers, data=verification_dict
    )
    response_dict = response.json()
    return response_dict


def to_verification_dict(webhook_headers, webhook_body):
    """Create the verification dict from a webhook's headers and event body.

    Docs: https://developer.paypal.com/api/webhooks/v1/#verify-webhook-signature_post
    """
    mapping = [
        ("transmission_id", "PayPal-Transmission-Id"),
        ("transmission_time", "PayPal-Transmission-Time"),
        ("cert_url", "PayPal-Cert-Url"),
        ("auth_algo", "PayPal-Auth-Algo"),
        ("transmission_sig", "PayPal-Transmission-Sig"),
    ]

    verification_dict = {
        verification_key: webhook_headers[header_received]
        for verification_key, header_received in mapping
    }

    # Hardcoded webhook ID from developer.paypal.com
    verification_dict["webhook_id"] = current_app.config["WEBHOOK_ID"]
    verification_dict["webhook_event"] = webhook_body

    return verification_dict


@bp.route("/", methods=("POST",))
def listener():
    webhook_body = request.json()
    current_app.logger.info(f"Webhook received:\n{json.dumps(webhook_body, indent=2)}")

    webhook_headers = request.headers

    verification_dict = to_verification_dict(webhook_headers, webhook_body)
    resp = verify_webhook_signature(verification_dict)

    if resp.get("verification_status") == "SUCCESS":
        print("Verification successful!")
    else:
        print("Verification unsuccessful. Response dict:")
        print(json.dumps(resp, indent=2))
