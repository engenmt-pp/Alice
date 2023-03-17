import json

from flask import Blueprint, current_app, render_template, url_for
from .api.identity import generate_client_token
from .api.orders import (
    get_order_details,
    get_payment_tokens,
    get_transactions,
    refund_order,
)

bp = Blueprint("store", __name__, url_prefix="/store")


def apple_pie():
    return {
        "name": "An apple pie",
        "description": "It's a pie made from apples.",
        "price": 3.14,
    }


@bp.route("/branded")
def checkout_branded():
    template = "checkout-branded.html"
    return checkout(template)


@bp.route("/branded-ba")
def checkout_branded_ba():
    template = "checkout-branded-ba.html"
    return checkout(template)


@bp.route("/branded-auth-capture")
def checkout_branded_auth_capture():
    template = "checkout-branded-auth-capture.html"
    return checkout(template)


@bp.route("/branded-vaulting")
def landing_branded_vaulting():
    return render_template("landing-branded-vaulting.html")


@bp.route("/branded-vaulting/<customer_id>")
def checkout_branded_vaulting(customer_id):
    client_token = generate_client_token(customer_id)
    template = "checkout-branded-vaulting.html"
    return checkout(template, customer_id=customer_id, client_token=client_token)


@bp.route("/hosted")
def checkout_hosted_fields():
    client_token = generate_client_token()
    template = "checkout-hosted.html"
    return checkout(template, client_token=client_token)


@bp.route("/hosted-vaulting")
def landing_hosted_vaulting():
    return render_template("landing-hosted-vaulting.html")


@bp.route("/checkout-not-present/<customer_id>")
def checkout_not_present(customer_id):
    template = "checkout-not-present.html"
    return checkout(template, customer_id=customer_id)


@bp.route("/orders")
def checkout_orders():
    template = "checkout-orders.html"
    return checkout(template)


@bp.route("/orders-vaulting/<customer_id>")
def checkout_orders_vaulting(customer_id):
    template = "checkout-orders-vaulting.html"
    return checkout(template, customer_id=customer_id)


@bp.route("/checkout-api")
def checkout_ship_api():
    template = "checkout-ship-api.html"
    return checkout(template)


@bp.route("/checkout-sdk")
def checkout_ship_sdk():
    template = "checkout-ship-sdk.html"
    return checkout(template)


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

    product = apple_pie()

    return render_template(
        template,
        product=product,
        partner_id=partner_id,
        partner_client_id=partner_client_id,
        payee_id=payee_id,
        bn_code=bn_code,
        **kwargs,
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


@bp.route("/payment-tokens/<customer_id>")
def payment_tokens(customer_id):
    tokens = get_payment_tokens(customer_id)
    status = json.dumps(tokens.json(), indent=2)
    return render_template("status.html", status=status)


@bp.route("/order-refund/<order_id>")
def order_refund(order_id):
    order_details = get_order_details(order_id)
    try:
        capture_id = order_details["purchase_units"][0]["payments"]["captures"][0]["id"]
    except (IndexError, KeyError) as exc:
        current_app.logger.error(
            f"Encountered {exc} while trying to extract capture ID from the below order details!"
        )
        current_app.logger.error(json.dumps(order_details, indent=2))
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
