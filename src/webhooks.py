import json

from flask import Blueprint, current_app, request

from .api import verify_webhook_signature


bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")


def to_verification_dict(webhook_headers, webhook_body, webhook_id=None):
    """Create the verification dict from a webhook's headers and event body.

    Docs: https://developer.paypal.com/api/webhooks/v1/#verify-webhook-signature_post
    """
    if webhook_id is None:
        webhook_id = current_app.config["WEBHOOK_ID"]

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
    verification_dict["webhook_id"] = webhook_id
    verification_dict["webhook_event"] = webhook_body

    return verification_dict


@bp.route("/", methods=("POST",))
def listener():

    webhook_body = request.json
    print(f"Webhook received:\n{json.dumps(webhook_body, indent=2)}")

    webhook_headers = request.headers

    verification_dict = to_verification_dict(webhook_headers, webhook_body)
    resp = verify_webhook_signature(verification_dict)

    if resp.get("verification_status") == "SUCCESS":
        print("Verification successful!")
    else:
        print("Verification unsuccessful. Response dict:")
        print(json.dumps(resp, indent=2))
