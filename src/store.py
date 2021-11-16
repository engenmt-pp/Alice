import json

from .api import get_order_details, refund_order, get_transactions
from .my_secrets import PARTNER_CLIENT_ID
from flask import Blueprint, render_template, url_for

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
def order_details(order_id, **kwargs):
    order_details_dict = get_order_details(order_id)
    order_details_str = json.dumps(order_details_dict, indent=2)
    try:
        status_str = f"Order {order_details_dict['status'].lower()}!"
    except KeyError as exc:
        print(f"Tried to find 'status' of the below order:\n{order_details_str}.")
        raise exc

    return render_template(
        "status.html", status=order_details_str, contexts=[status_str], **kwargs
    )


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
    return order_details(order_id, contexts=["Refund initiated!"])


@bp.route("/recent-orders")
def recent_orders():
    transactions = get_transactions()

    # verbose = True
    verbose = False
    if verbose:
        for t in transactions["transaction_details"]:
            print(json.dumps(t, indent=2))
            print()

    transactions_list = [
        t["transaction_info"] for t in transactions["transaction_details"][::-1]
    ]
    # transaction_list is in reverse-chronological order now.

    status_dict = {"D": "Denied", "P": "Pending", "S": "Successful", "V": "Reversed"}

    type_dict = {
        "ODR": "Order",
        "TXN": "Transaction",
        "SUB": "Subscription",
        "PAP": "Pre-approved Payment",
        "UNK": "Unknown",
    }

    for t in transactions_list:
        t["status"] = status_dict[t["transaction_status"]]
        ref_id_type = t.get("paypal_reference_id_type", "UNK")
        t["type"] = type_dict[ref_id_type]

        if t["type"] == "Order":
            id = t["transaction_id"]
            # id = t.get("paypal_reference_id", t["transaction_id"])
            t["refund_link"] = url_for("store.order_refund", order_id=id)
            t["status_link"] = url_for("store.order_details", order_id=id)
        else:
            t["refund_link"] = ""
            t["status_link"] = ""

    return render_template("transactions.html", transactions=transactions_list)
