import json

from .api import get_order_details
from .my_secrets import PARTNER_CLIENT_ID, PARTNER_BN_CODE, MERCHANT_ID
from flask import Blueprint, render_template

bp = Blueprint("store", __name__, url_prefix="/store")


def apple_pie():
    return {
        "name": "An apple pie",
        "description": "It's a pie made from apples.",
        "price": 3.14,
    }


@bp.route("/checkout")
def checkout():
    product = apple_pie()

    return render_template(
        # "checkout-ship-api.html",
        "checkout-ship-sdk.html",
        product=product,
        partner_client_id=PARTNER_CLIENT_ID,
        payee_merchant_id=MERCHANT_ID,
        bn_code=PARTNER_BN_CODE,
    )


@bp.route("/checkout-js")
def checkout_ship_js_sdk():
    product = apple_pie()

    return render_template(
        "checkout-ship-sdk.html",
        product=product,
        partner_client_id=PARTNER_CLIENT_ID,
        payee_merchant_id=MERCHANT_ID,
        bn_code=PARTNER_BN_CODE,
    )


@bp.route("/order-details/<order_id>")
def order_details(order_id):
    order_details_dict = get_order_details(order_id)
    order_details_str = json.dumps(order_details_dict, indent=2)
    return render_template("status.html", status=order_details_str)
