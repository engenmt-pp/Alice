import json

from flask import Blueprint, current_app, render_template, request

bp = Blueprint("statuses", __name__, url_prefix="/statuses")


@bp.route("/")
def statuses():
    template = "statuses.html"

    partner_id = request.args.get("partner-id", current_app.config["PARTNER_ID"])
    partner_client_id = request.args.get(
        "partner-client-id", current_app.config["PARTNER_CLIENT_ID"]
    )
    merchant_id = request.args.get("merchant-id", current_app.config["MERCHANT_ID"])
    bn_code = request.args.get("bn-code", current_app.config["PARTNER_BN_CODE"])

    return render_template(
        template,
        partner_id=partner_id,
        partner_client_id=partner_client_id,
        merchant_id=merchant_id,
        bn_code=bn_code,
    )
