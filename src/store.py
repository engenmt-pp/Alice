import json

from .api import get_order_details, refund_order
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
        payee_merchant_id=PAYEE_MERCHANT_ID,
        bn_code=MERCHANT_BN_CODE,
    )


@bp.route("/order-details/<order_id>")
def order_details(order_id):
    order_details_dict = get_order_details(order_id)
    order_details_str = json.dumps(order_details_dict, indent=2)
    return render_template("status.html", status=order_details_str)


@bp.route("/order-refund/<order_id>")
def order_refund(order_id):
    order_details = get_order_details(order_id)
    try:
        capture_id = order_details["purchase_units"][0]["payments"]["captures"][0]["id"]
    except (IndexError, KeyError) as exc:
        print(
            f"Encountered {exc} while trying to extract capture ID from the below order details!"
        )
        print(json.dumps(order_details, indent=2))
        raise exc
    refund_order(capture_id)

    # This will intentionally poll the order status again
    return order_details(order_id)
