from flask import Blueprint, current_app, render_template

bp = Blueprint("checkout", __name__, url_prefix="/checkout")


@bp.route("/")
def checkout_branded():
    template = "checkout.html"
    return checkout(template)


def checkout(
    template,
    partner_id=None,
    partner_client_id=None,
    merchant_id=None,
    partner_bn_code=None,
    **kwargs,
):
    partner_id = partner_id or current_app.config["PARTNER_ID"]
    partner_client_id = partner_client_id or current_app.config["PARTNER_CLIENT_ID"]
    partner_bn_code = partner_bn_code or current_app.config["PARTNER_BN_CODE"]
    merchant_id = merchant_id or current_app.config["MERCHANT_ID"]

    return render_template(
        template,
        partner_id=partner_id,
        partner_client_id=partner_client_id,
        merchant_id=merchant_id,
        partner_bn_code=partner_bn_code,
        **kwargs,
    )
