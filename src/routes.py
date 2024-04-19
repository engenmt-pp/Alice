from flask import Blueprint, current_app, render_template, request

bp = Blueprint("routes", __name__, url_prefix="/")


def get_credentials(ppcp_type):
    ppcp_type = ppcp_type or request.args.get("ppcpType") or "partner"
    match ppcp_type:
        case "partner":
            credentials = {
                "partner_id": current_app.config["PARTNER_ID"],
                "client_id": current_app.config["PARTNER_CLIENT_ID"],
                "bn_code": current_app.config["PARTNER_BN_CODE"],
                "merchant_id": current_app.config["MERCHANT_ID"],
                "ppcp_type": ppcp_type,
            }
        case "merchant":
            credentials = {
                "merchant_id": current_app.config["MERCHANT_ID"],
                "client_id": current_app.config["MERCHANT_CLIENT_ID"],
                "ppcp_type": ppcp_type,
            }
    return credentials


@bp.route("onboarding/")
def onboarding():
    """Return the rendered onboarding page from its template."""

    template = "onboarding.html"
    credentials = get_credentials("partner")
    del credentials["merchant_id"]

    return render_template(
        template,
        **credentials,
        favicon=current_app.config["favicon"],
    )


@bp.route("")
@bp.route("checkout/", endpoint="checkout-canonical")
@bp.route("checkout/branded/")
def checkout_branded(ppcp_type=None):
    """Return the rendered Branded checkout page from its template."""

    template = "checkout-branded.html"
    credentials = get_credentials(ppcp_type)

    return render_template(
        template,
        method="branded",
        **credentials,
        favicon=current_app.config["favicon"],
    )


@bp.route("checkout/google-pay/")
def checkout_google_pay(ppcp_type=None):
    """Return the rendered Google Pay checkout page from its template."""

    template = "checkout-google-pay.html"
    credentials = get_credentials(ppcp_type)

    return render_template(
        template,
        method="google-pay",
        **credentials,
        favicon=current_app.config["favicon"],
    )


@bp.route("checkout/hosted-v1/")
def checkout_hosted_v1(ppcp_type=None):
    """Return the rendered Hosted Fields v1 checkout page from its template."""

    template = "checkout-hf-v1.html"
    credentials = get_credentials(ppcp_type)

    return render_template(
        template,
        method="hosted-v1",
        **credentials,
        favicon=current_app.config["favicon"],
    )


@bp.route("checkout/hosted-v2/")
def checkout_hosted_v2(ppcp_type=None):
    """Return the rendered Hosted Fields v2 checkout page from its template."""

    template = "checkout-hf-v2.html"
    credentials = get_credentials(ppcp_type)

    return render_template(
        template,
        method="hosted-v2",
        **credentials,
        favicon=current_app.config["favicon"],
    )


@bp.route("statuses/")
def statuses(ppcp_type=None):
    """Return the rendered statuses page from its template."""

    template = "statuses.html"
    credentials = get_credentials(ppcp_type)

    return render_template(
        template,
        **credentials,
        favicon=current_app.config["favicon"],
    )
