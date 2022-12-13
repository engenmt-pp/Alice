from flask import Blueprint, current_app, render_template
from .api.utils import (
    generate_client_token,
)

bp = Blueprint("store_form", __name__, url_prefix="/store-form")


@bp.route("/branded")
def checkout_branded():
    template = "checkout-form-branded.html"
    return checkout(template)


@bp.route("/branded-ba")
def checkout_branded_ba():
    template = "checkout-form-branded-ba.html"
    return checkout(template)


@bp.route("/hosted")
def checkout_hosted_fields():
    client_token_response = generate_client_token(return_formatted=True)
    client_token = client_token_response["client_token"]
    formatted_calls = client_token_response["formatted"]
    template = "checkout-form-hosted.html"
    return checkout(
        template,
        client_token=client_token,
        formatted_calls=formatted_calls,
    )


def checkout(
    template,
    partner_id=None,
    partner_client_id=None,
    payee_id=None,
    bn_code=None,
    **kwargs,
):
    if partner_id is None:
        partner_id = current_app.config["PARTNER_ID"]
    if partner_client_id is None:
        partner_client_id = current_app.config["PARTNER_CLIENT_ID"]
    if payee_id is None:
        payee_id = current_app.config["MERCHANT_ID"]
    if bn_code is None:
        bn_code = current_app.config["PARTNER_BN_CODE"]

    return render_template(
        template,
        partner_id=partner_id,
        partner_client_id=partner_client_id,
        payee_id=payee_id,
        bn_code=bn_code,
        **kwargs,
    )
