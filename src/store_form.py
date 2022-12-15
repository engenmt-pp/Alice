from flask import Blueprint, current_app, render_template, request
from .api.utils import (
    build_script_tag,
    generate_client_token,
)

bp = Blueprint("store_form", __name__, url_prefix="/store-form")


@bp.route("/branded")
def checkout_branded():
    template = "checkout-form-branded.html"
    additional_query = {
        "commit": "true",
        "enable-funding": "venmo,paylater",
    }
    return checkout(template, additional_query=additional_query)


@bp.route("/branded-ba")
def checkout_branded_ba():
    template = "checkout-form-branded-ba.html"
    intent = "tokenize"
    # intent = "capture"
    additional_query = {"commit": "true", "vault": "true"}
    return checkout(template, intent=intent, additional_query=additional_query)


@bp.route("/hosted")
def checkout_hosted_fields():
    template = "checkout-form-hosted.html"
    client_token_response = generate_client_token(return_formatted=True)
    client_token = client_token_response["client_token"]
    formatted_calls = client_token_response["formatted"]

    additional_query = {"components": "hosted-fields"}
    return checkout(
        template,
        client_token=client_token,
        formatted_calls=formatted_calls,
        additional_query=additional_query,
    )


def checkout(
    template,
    additional_query=None,
    client_token=None,
    **kwargs,
):
    partner_id = request.args.get("partner-id", current_app.config["PARTNER_ID"])
    partner_client_id = request.args.get(
        "partner-client-id", current_app.config["PARTNER_CLIENT_ID"]
    )
    merchant_id = request.args.get("merchant-id", current_app.config["MERCHANT_ID"])
    bn_code = request.args.get("bn-code", current_app.config["PARTNER_BN_CODE"])

    intent = request.args.get("intent", kwargs.get("intent", "capture"))
    script_tag = build_script_tag(
        partner_client_id,
        merchant_id,
        intent,
        bn_code,
        additional_query,
        client_token=client_token,
    )

    return render_template(
        template,
        partner_id=partner_id,
        partner_client_id=partner_client_id,
        merchant_id=merchant_id,
        script_tag=script_tag,
        **kwargs,
    )
