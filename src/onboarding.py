from flask import Blueprint, current_app, render_template

bp = Blueprint("onboarding", __name__, url_prefix="/onboarding")


@bp.route("/")
def onboarding():
    partner_id = current_app.config["PARTNER_ID"]
    partner_client_id = current_app.config["PARTNER_CLIENT_ID"]
    partner_bn_code = current_app.config["PARTNER_BN_CODE"]
    return render_template(
        "onboarding.html",
        partner_id=partner_id,
        partner_client_id=partner_client_id,
        bn_code=partner_bn_code,
    )
