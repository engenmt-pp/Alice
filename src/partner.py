import json
import secrets

from flask import Blueprint, render_template, url_for
from .api import generate_sign_up_link, get_merchant_id, get_status

bp = Blueprint("partner", __name__, url_prefix="/partner")


def generate_tracking_id():
    """Generate a `length`-length hexadecimal tracking_id.

    Collisions are unlikely (1 in 281_474_976_710_656 chance)."""
    length = 12
    return secrets.token_hex(length)


@bp.route("/sign-up")
def sign_up():
    tracking_id = generate_tracking_id()
    sign_up_link = generate_sign_up_link(tracking_id)

    # Get the URL for the corresponding status page
    tracking_url = url_for("partner.status", tracking_id=tracking_id)

    return render_template(
        "sign_up.html", sign_up_link=sign_up_link, tracking_url=tracking_url
    )


def is_ready_to_transact(status):
    """Return whether or not the merchant is ready to process transactions based on its status.

    As the requested features list is hardcoded as [
        "PAYMENT",
        "REFUND",
        "PARTNER_FEE",
        "DELAY_FUNDS_DISBURSEMENT",
    ],
    we can just check for the corresponding URLs in the third party scopes.
    """
    scopes_required = [
        "https://uri.paypal.com/services/payments/realtimepayment",
        "https://uri.paypal.com/services/payments/payment/authcapture",
        "https://uri.paypal.com/services/payments/refund",
        "https://uri.paypal.com/services/payments/partnerfee",
        "https://uri.paypal.com/services/payments/delay-funds-disbursement",
    ]
    try:
        oauth_integrations = status["oauth_integrations"][0]
        scopes_present = oauth_integrations["oauth_third_party"][0]["scopes"]
    except (IndexError, KeyError):
        return False

    return (
        status["payments_receivable"]
        and status["primary_email_confirmed"]
        and all(required_scope in scopes_present for required_scope in scopes_required)
    )


def parse_vetting_status(status):
    for product in status["products"]:
        if product["name"] == "PPCP_CUSTOM":
            vetting_status = product["vetting_status"]
            break
    else:
        # If we're here, PPCP_CUSTOM wasn't found!
        return "PPCP_CUSTOM is not a registered product!"

    if vetting_status == "DENIED":
        return "Enable PayPal Payment Buttons!"
    elif vetting_status == "SUBSCRIBED":
        has_inactive_capabilities = any(
            capability["status"] != "ACTIVE" for capability in status["capabilities"]
        )
        if has_inactive_capabilities:
            return (
                "Enable PayPal Payment Buttons and wait for "
                "CUSTOMER.MERCHANT-INTEGRATION.CAPABILITY-UPDATED webhook!"
            )

        return "Enable Advanced Card Processing!"
    else:
        if status["primary_email_confirmed"]:
            return (
                "Enable PayPal Payment Buttons and wait for "
                "CUSTOMER.MERCHANT-INTEGRATION.PRODUCT-SUBSCRIPTION-UPDATED webhook!"
            )
        return "Something is wrong with PPCP_CUSTOM!"


@bp.route("/status/<tracking_id>")
def status(tracking_id):
    merchant_id = get_merchant_id(tracking_id)
    status = get_status(merchant_id)
    status_text = json.dumps(status, indent=2)

    is_ready = is_ready_to_transact(status)
    contexts = [
        f"Ready to transact: {is_ready}",
        f"Partner should: {parse_vetting_status(status)}",
    ]
    return render_template("status.html", status=status_text, contexts=contexts)
