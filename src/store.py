import json

from flask import Blueprint, current_app, render_template
from .api import get_order_details, generate_client_token, list_payment_tokens

bp = Blueprint("store", __name__, url_prefix="/store")


@bp.route("/checkout")
def checkout_capture():
    template = "checkout.html"
    return checkout(template)


@bp.route("/checkout-auth")
def checkout_authorize():
    template = "checkout-auth-capture.html"
    return checkout(template)


def checkout(template, partner_client_id=None, payee_id=None, bn_code=None):
    if partner_client_id is None:
        partner_client_id = current_app.config["PARTNER_CLIENT_ID"]
    if payee_id is None:
        payee_id = current_app.config["MERCHANT_ID"]
    if bn_code is None:
        bn_code = current_app.config["PARTNER_BN_CODE"]

    product = {
        "name": "An apple pie",
        "description": "It's a pie made from apples.",
        "price": 3.14,
    }

    return render_template(
        template,
        product=product,
        partner_client_id=partner_client_id,
        payee_id=payee_id,
        bn_code=bn_code,
    )


@bp.route("/vaulting")
def checkout_vaulting(
    partner_client_id=None, payee_id=None, bn_code=None, client_token=None
):
    if partner_client_id is None:
        partner_client_id = current_app.config["PARTNER_CLIENT_ID"]
    if payee_id is None:
        payee_id = current_app.config["MERCHANT_ID"]
    if bn_code is None:
        bn_code = current_app.config["PARTNER_BN_CODE"]
    if client_token is None:
        client_token = generate_client_token()

    product = {
        "name": "An apple pie",
        "description": "It's a pie made from apples.",
        "price": 3.14,
    }

    return render_template(
        "checkout-vaulting.html",
        product=product,
        partner_client_id=partner_client_id,
        payee_id=payee_id,
        bn_code=bn_code,
        client_token=client_token,
    )


@bp.route("/vaulting")
def checkout_vaulting(
    partner_client_id=None, payee_id=None, bn_code=None, client_token=None
):
    if partner_client_id is None:
        partner_client_id = current_app.config["PARTNER_CLIENT_ID"]
    if payee_id is None:
        payee_id = current_app.config["MERCHANT_ID"]
    if bn_code is None:
        bn_code = current_app.config["PARTNER_BN_CODE"]
    if client_token is None:
        client_token = generate_client_token()

    product = {
        "name": "An apple pie",
        "description": "It's a pie made from apples.",
        "price": 3.14,
    }

    return render_template(
        "checkout-vaulting.html",
        product=product,
        partner_client_id=partner_client_id,
        payee_id=payee_id,
        bn_code=bn_code,
        client_token=client_token,
    )


@bp.route("/order-details/<order_id>")
def order_details(order_id):
    order_details_dict = get_order_details(order_id)
    order_details_str = json.dumps(order_details_dict, indent=2)
    return render_template("status.html", status=order_details_str)


@bp.route("/payment-tokens")
def payment_tokens(customer_id=None):
    tokens = list_payment_tokens(customer_id=customer_id)
    # return render_template("status.html", status=json.dumps(tokens))
    return render_template("status.html", status=tokens.text)
