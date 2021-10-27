import json

from .api import generate_sign_up_link, get_merchant_id, get_status, url_for

from flask import Blueprint, render_template

bp = Blueprint("partner", __name__, url_prefix="/partner")


@bp.route("/sign-up")
def sign_up(tracking_id="8675309"):
    sign_up_link = generate_sign_up_link(tracking_id)

    # Get the URL for the corresponding status page
    tracking_url = url_for("status", tracking_id=tracking_id)

    return render_template(
        "sign_up.html", sign_up_link=sign_up_link, tracking_url=tracking_url
    )


@bp.route("/status/<tracking_id>")
def status(tracking_id):
    merchant_id = get_merchant_id(tracking_id)
    status = get_status(merchant_id)
    status_text = json.dumps(status, indent=2)
    return render_template("status.html", status=status_text)


# , methods=("GET",)
# , methods=("GET",)
