import json

from flask import Blueprint, request

from .api import verify_webhook_signature
from .my_secrets import WEBHOOK_ID


bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")


def to_verification_dict(webhook_headers, webhook_body):
    """Create the verification dict from a webhook's headers and event body.

    Docs: https://developer.paypal.com/api/webhooks/v1/#verify-webhook-signature_post
    """
    mapping = [
        ("Paypal-Transmission-Id", "transmission_id"),
        ("Paypal-Transmission-Time", "transmission_time"),
        ("Paypal-Cert-Url", "cert_url"),
        ("Paypal-Auth-Algo", "auth_algo"),
        ("Paypal-Transmission-Sig", "transmission_sig"),
    ]

    verification_dict = {
        verification_key: webhook_headers[header_received]
        for header_received, verification_key in mapping
    }

    verification_dict[
        "webhook_id"
    ] = WEBHOOK_ID  # Hardcoded ID for the webhook from developer.paypal.com
    verification_dict["webhook_event"] = webhook_body


@bp.route("/", methods=("POST",))
def listener():
    print(f"Webhook received!")

    webhook_headers = dict(request.headers)
    webhook_body = request.json

    verification_dict = to_verification_dict(webhook_headers, webhook_body)
    resp = verify_webhook_signature(verification_dict)
    if resp.get("verification_status") == "SUCCESS":
        print(f"Successfully verified webhook signature!")
    else:
        print(f"Verification unsuccessful. Response dict:\n{json.dumps(resp,indent=2)}")

    print(f"Webhook JSON = {json.dumps(webhook_body, indent=2)}")

    return "", 204
