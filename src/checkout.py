from flask import Blueprint, current_app, render_template

bp = Blueprint("checkout", __name__, url_prefix="/checkout")


@bp.route("/")
def checkout():
    """Return the rendered checkout page from its template."""

    template = "checkout.html"

    partner_and_merchant_config = {
        "partner_id": current_app.config["PARTNER_ID"],
        "partner_client_id": current_app.config["PARTNER_CLIENT_ID"],
        "partner_bn_code": current_app.config["PARTNER_BN_CODE"],
        "merchant_id": current_app.config["MERCHANT_ID"],
    }

    return render_template(template, **partner_and_merchant_config)
