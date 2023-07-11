from flask import Blueprint, current_app, render_template

bp = Blueprint("checkout", __name__, url_prefix="/checkout")


@bp.route("/")
def checkout():
    template = "checkout.html"
    partner_id = current_app.config["PARTNER_ID"]
    partner_client_id = current_app.config["PARTNER_CLIENT_ID"]
    partner_bn_code = current_app.config["PARTNER_BN_CODE"]
    merchant_id = current_app.config["MERCHANT_ID"]

    return render_template(
        template,
        partner_id=partner_id,
        partner_client_id=partner_client_id,
        merchant_id=merchant_id,
        partner_bn_code=partner_bn_code,
    )
