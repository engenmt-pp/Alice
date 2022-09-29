import json

from flask import Blueprint, current_app, render_template, url_for
from .api.charities import get_charities

bp = Blueprint("charities", __name__, url_prefix="/charities")


@bp.route("/")
def charities_list():
    charities = get_charities()
    charities_str = json.dumps(charities.json(), indent=2)
    return render_template("status.html", status=charities_str, contexts=[])


@bp.route("/recent-orders")
def recent_orders():
    transactions = get_transactions()

    # verbose = True
    verbose = False
    if verbose:
        try:
            for t in transactions["transaction_details"]:
                print(json.dumps(t, indent=2))
                print()
        except Exception as exc:
            print(f"Encountered {exc}!")
            print(f"Transactions received: {json.dumps(transactions, indent=2)}")
            raise exc

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

        id = t["transaction_id"]
        # id = t.get("paypal_reference_id", t["transaction_id"])
        t["refund_link"] = url_for("store.order_refund", order_id=id)
        t["status_link"] = url_for("store.order_details", order_id=id)
        # if t["type"] == "Order":
        #     id = t["transaction_id"]
        #     # id = t.get("paypal_reference_id", t["transaction_id"])
        #     t["refund_link"] = url_for("store.order_refund", order_id=id)
        #     t["status_link"] = url_for("store.order_details", order_id=id)
        # else:
        #     print(f"Transaction is not an order: {json.dumps(t,indent=2)}")
        #     t["refund_link"] = ""
        #     t["status_link"] = ""

    return render_template("transactions.html", transactions=transactions_list)
