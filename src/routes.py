from flask import Blueprint, current_app, render_template, request

bp = Blueprint("routes", __name__, url_prefix="/")


def get_partner_and_merchant_config():
    partner_and_merchant_config = {
        "partner_id": request.args.get("partner-id", current_app.config["PARTNER_ID"]),
        "partner_client_id": request.args.get(
            "partner-client-id", current_app.config["PARTNER_CLIENT_ID"]
        ),
        "partner_bn_code": request.args.get(
            "bn-code", current_app.config["PARTNER_BN_CODE"]
        ),
        "merchant_id": request.args.get(
            "merchant-id", current_app.config["MERCHANT_ID"]
        ),
    }
    return partner_and_merchant_config


@bp.route("onboarding/")
def onboarding():
    """Return the rendered onboarding page from its template."""

    partner_config = get_partner_and_merchant_config()
    del partner_config["merchant_id"]

    return render_template(
        "onboarding.html", **partner_config, favicon=current_app.config["favicon"]
    )


@bp.route("")
@bp.route("checkout/")
def checkout():
    """Return the rendered checkout page from its template."""

    template = "checkout.html"

    partner_and_merchant_config = get_partner_and_merchant_config()

    return render_template(
        template, **partner_and_merchant_config, favicon=current_app.config["favicon"]
    )


@bp.route("statuses/")
def statuses():
    """Return the rendered statuses page from its template."""

    template = "statuses.html"

    partner_and_merchant_config = get_partner_and_merchant_config()

    return render_template(
        template, **partner_and_merchant_config, favicon=current_app.config["favicon"]
    )
