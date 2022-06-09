import json
import secrets

from flask import Blueprint, render_template, url_for
from .api import (
    generate_onboarding_urls,
    get_merchant_id,
    get_onboarding_status,
    get_referral_status,
    get_partner_referral_id,
)

bp = Blueprint("partner", __name__, url_prefix="/partner")


def generate_tracking_id():
    """Generate a `length`-length hexadecimal tracking_id.

    Collisions are unlikely (1 in 281_474_976_710_656 chance)."""
    length = 12
    return secrets.token_hex(length)


@bp.route("/onboarding")
def onboarding(version="v2"):
    tracking_id = generate_tracking_id()
    onboarding_url, referral_url = generate_onboarding_urls(
        tracking_id, version=version
    )

    # Get the URL for the referral status page
    partner_referral_id = get_partner_referral_id(referral_url)
    referral_status_url = url_for(
        "partner.referral_status", partner_referral_id=partner_referral_id
    )

    # Get the URL for the onboarding status page
    onboarding_status_url = url_for(
        "partner.onboarding_status_tracking", tracking_id=tracking_id
    )

    return render_template(
        "onboarding.html",
        onboarding_url=onboarding_url,
        referral_status_url=referral_status_url,
        onboarding_status_url=onboarding_status_url,
    )


def is_ready_to_transact(status):
    """Return whether or not the merchant is ready to process transactions based on the merchant's status.

    As the requested features list is hardcoded as [
        "PAYMENT",
        "REFUND",
        "PARTNER_FEE",
        "DELAY_FUNDS_DISBURSEMENT",
        "ADVANCED_TRANSACTIONS_SEARCH",
    ],
    we can just check for the corresponding URLs in the third party scopes.
    """
    scopes_required = [
        "https://uri.paypal.com/services/payments/realtimepayment",
        "https://uri.paypal.com/services/payments/payment/authcapture",
        "https://uri.paypal.com/services/payments/refund",
        "https://uri.paypal.com/services/payments/partnerfee",
        "https://uri.paypal.com/services/payments/delay-funds-disbursement",
        "https://uri.paypal.com/services/reporting/search/read",  # Present if "ADVANCED_TRANSACTIONS_SEARCH" is included
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
    """Return instructions for the partner given the vetting status of an onboarded merchant."""
    for product in status["products"]:
        if product["name"] == "PPCP_CUSTOM":
            vetting_status = product["vetting_status"]
            break
    else:
        # If we're here, PPCP_CUSTOM wasn't found!
        return "PPCP_CUSTOM is not a registered product!"

    if not status["primary_email_confirmed"]:
        return "Ask merchant to confirm their primary email address!"

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

    return "PPCP_CUSTOM is neither 'DENIED' nor 'SUBSCRIBED'!"


@bp.route("/onboarding/tracking/<tracking_id>")
def onboarding_status_tracking(tracking_id):
    merchant_id = get_merchant_id(tracking_id)
    return onboarding_status(merchant_id)


@bp.route("/onboarding/<merchant_id>")
def onboarding_status(merchant_id):
    status = get_onboarding_status(merchant_id)

    is_ready = is_ready_to_transact(status)
    contexts = [
        f"Ready to transact: {is_ready}",
        f"Partner should: {parse_vetting_status(status)}",
    ]

    status_text = json.dumps(status, indent=2)
    return render_template("status.html", status=status_text, contexts=contexts)


@bp.route("/referral/<partner_referral_id>")
def referral_status(partner_referral_id):

    referral_status_dict = get_referral_status(partner_referral_id)
    status_text = json.dumps(referral_status_dict, indent=2)

    return render_template("status.html", status=status_text, contexts=[])
