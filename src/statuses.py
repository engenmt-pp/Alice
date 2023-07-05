from flask import Blueprint, current_app, render_template, request

bp = Blueprint("statuses", __name__, url_prefix="/statuses")


@bp.route("/")
def statuses():
    """Return the rendered statuses page from its template."""

    template = "statuses.html"

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

    return render_template(template, **partner_and_merchant_config)
