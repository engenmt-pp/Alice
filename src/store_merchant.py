import json

from flask import Blueprint, current_app, render_template
from .store import apple_pie
from .api.utils import (
    generate_client_token,
)
from .api.orders_merchant import (
    get_order_details,
    get_payment_tokens,
)

bp = Blueprint("store_merchant", __name__, url_prefix="/store-merchant")


@bp.route("/checkout-vault/<customer_id>")
def checkout_vaulting(customer_id):
    client_token = generate_client_token(customer_id)
    template = "checkout-vaulting-merchant.html"
    return checkout(template, customer_id=customer_id, client_token=client_token)


def checkout(template, merchant_client_id=None, payee_id=None, **kwargs):
    if merchant_client_id is None:
        merchant_client_id = current_app.config["MERCHANT_CLIENT_ID"]
    if payee_id is None:
        payee_id = current_app.config["MERCHANT_ID"]

    product = apple_pie()

    return render_template(
        template,
        product=product,
        payee_id=payee_id,
        merchant_client_id=merchant_client_id,
        **kwargs,
    )


@bp.route("/order-details/<order_id>")
def order_details(order_id, **kwargs):
    order_details_dict = get_order_details(order_id)
    order_details_str = json.dumps(order_details_dict, indent=2)
    try:
        status_str = f"Order {order_details_dict['status'].lower()}!"
    except KeyError as exc:
        current_app.logger.error(
            f"Tried to find 'status' of the below order:\n{order_details_str}."
        )
        raise exc

    return render_template(
        "status.html", status=order_details_str, contexts=[status_str], **kwargs
    )


@bp.route("/payment-tokens/<customer_id>")
def payment_tokens(customer_id):
    tokens = get_payment_tokens(customer_id)
    status = json.dumps(tokens.json(), indent=2)
    return render_template("status.html", status=status)
