import json

from .api import get_order_details
from .my_secrets import PARTNER_CLIENT_ID, PARTNER_ID
from flask import Blueprint, render_template

bp = Blueprint("store", __name__, url_prefix="/store")

PAYEE_MERCHANT_ID = "NY9D8KUEC8W54"
MERCHANT_BN_CODE = "my_bn_code"


@bp.route("/checkout")
def checkout():
    product = {
        "name": "An apple pie",
        "description": "It's a pie made from apples.",
        "price": 3.14,
    }

    return render_template(
        "checkout.html",
        product=product,
        partner_client_id=PARTNER_CLIENT_ID,
        partner_merchant_id=PARTNER_ID,
        payee_merchant_id=PAYEE_MERCHANT_ID,
        bn_code=MERCHANT_BN_CODE,
    )


@bp.route("/order-details/<order_id>")
def order_details(order_id):
    order_details_dict = get_order_details(order_id)
    order_details_str = json.dumps(order_details_dict, indent=2)
    return render_template("status.html", status=order_details_str)
