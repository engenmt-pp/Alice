import json
import requests

from flask import Blueprint, request, current_app, jsonify

from .identity import build_headers
from .utils import build_endpoint, format_request_and_response


bp = Blueprint("orders", __name__, url_prefix="/orders")


class Order:
    def __init__(self, **kwargs):
        self.order_id = kwargs.get("order-id") or None  # Coerce to None if empty
        self.auth_id = kwargs.get("auth-id")

        self.auth_header = kwargs.get("authHeader")

        self.currency = kwargs.get("currency")
        self.intent = kwargs.get("intent")
        self.disbursement_mode = kwargs.get("disbursement-mode")

        self.reference_id = kwargs.get("reference-id")
        self.custom_id = kwargs.get("custom-id")
        self.soft_descriptor = kwargs.get("soft-descriptor")
        self.shipping_preference = kwargs.get("shipping-preference")

        self.vault_v3 = kwargs.get("vault-v3")
        self.vault_id = kwargs.get("vault-id")
        try:
            self.include_auth_assertion = bool(kwargs["include-auth-assertion"])
        except KeyError:
            self.include_auth_assertion = self.vault_v3 == "MERCHANT"
        self.include_payee = not self.include_auth_assertion
        self.include_request_id = True

        self.ba_id = kwargs.get("ba-id")

        self.partner_id = kwargs.get("partnerId")
        self.merchant_id = kwargs.get("merchantId")

        self.include_shipping_options = kwargs.get("include-shipping-options")
        self.shipping_cost = 9.99
        self.include_shipping_address = kwargs.get("include-shipping-address")

        self.partner_fee = float(kwargs.get("partner-fee", "0"))
        self.item_price = kwargs.get("item-price")
        self.item_tax = float(kwargs.get("item-tax", "0"))
        self.item_category = kwargs.get("item-category")

        self.formatted = dict()
        self.breakdown = dict()

    def to_amount_dict(self, amount):
        if isinstance(amount, str):
            amount = float(amount)
        return {
            "currency_code": self.currency,
            "value": amount,
        }

    def build_headers(self):
        """Wrapper for .utils.build_headers."""
        headers = build_headers(
            auth_header=self.auth_header,
            include_auth_assertion=self.include_auth_assertion,
            include_request_id=self.include_request_id,
            return_formatted=True,
        )
        if "formatted" in headers:
            self.formatted |= headers["formatted"]
            del headers["formatted"]

        self.auth_header = headers["Authorization"]
        return headers

    def build_platform_fees(self):
        platform_fees = []
        if self.partner_fee > 0:
            platform_fees.append(
                {
                    "amount": self.to_amount_dict(self.partner_fee),
                    "payee": {
                        "merchant_id": self.partner_id,
                    },
                }
            )
        return platform_fees

    def build_payment_instruction(self, for_call):
        """Return the payment instruction for the order."""
        payment_instruction = dict()

        match (self.intent, for_call):
            case ("CAPTURE", "create") | ("AUTHORIZE", "capture"):
                if self.disbursement_mode == "DELAYED":
                    payment_instruction["disbursement_mode"] = self.disbursement_mode

                platform_fees = self.build_platform_fees()
                if platform_fees:
                    payment_instruction["platform_fees"] = platform_fees

        return payment_instruction

    def build_shipping_option(self):
        return {
            "id": "shipping-default",
            "label": "A default shipping option",
            "selected": True,
            "amount": self.to_amount_dict(self.shipping_cost),
        }

    def build_shipping(self):
        """Return the shipping information for the order."""
        shipping = dict()

        if self.include_shipping_address:
            shipping |= {
                "name": {"full_name": "Myfuhl Name"},
                "address": {
                    "address_line_1": "1324 Permutation Pattern Parkway",
                    "admin_area_2": "Gainesville",
                    "admin_area_1": "FL",
                    "postal_code": "32601",
                    "country_code": "US",
                },
            }
            if not self.include_shipping_options:
                shipping["type"] = "SHIPPING"

        if self.include_shipping_options:
            shipping_options = [self.build_shipping_option()]
            shipping["options"] = shipping_options
            self.breakdown["shipping"] = self.to_amount_dict(self.shipping_cost)

        return shipping

    def build_line_item(self):
        """Return the line item object."""
        match self.item_category:
            case "PHYSICAL_GOODS":
                name = "A physical good."
            case "DIGITAL_GOODS":
                name = "A digital good."
            case "DONATION":
                name = "A donation."
            case None | "None":
                name = "A good of unspecified category."
                self.item_category = None
            case _:
                raise ValueError

        unit_amount = self.to_amount_dict(self.item_price)
        item = {
            "name": name,
            "quantity": 1,
            "unit_amount": unit_amount,
        }
        self.breakdown["item_total"] = unit_amount

        if self.item_category is not None:
            item["category"] = self.item_category

        if self.item_tax:
            tax_amount = self.to_amount_dict(self.item_tax)
            item["tax"] = tax_amount
            self.breakdown["tax_total"] = tax_amount

        return item

    def build_purchase_unit(self):
        purchase_unit = dict()
        if self.include_payee:
            purchase_unit["payee"] = {"merchant_id": self.merchant_id}

        if self.reference_id:
            purchase_unit["reference_id"] = self.reference_id
        if self.custom_id:
            purchase_unit["custom_id"] = self.custom_id
        if self.soft_descriptor:
            purchase_unit["soft_descriptor"] = self.soft_descriptor

        payment_instruction = self.build_payment_instruction(for_call="create")
        if payment_instruction:
            purchase_unit["payment_instruction"] = payment_instruction

        shipping = self.build_shipping()
        if shipping:
            purchase_unit["shipping"] = shipping

        purchase_unit["items"] = [self.build_line_item()]
        total_price = round(
            sum(float(cost["value"]) for cost in self.breakdown.values()), 2
        )
        amount = self.to_amount_dict(total_price) | {"breakdown": self.breakdown}
        purchase_unit["amount"] = amount
        return purchase_unit

    def build_context(self):
        context = {
            "return_url": "http://go/alice/return",
            "cancel_url": "http://go/alice/cancel",
        }
        if self.shipping_preference:
            context["shipping_preference"] = self.shipping_preference
        return context

    def build_payment_source(self):
        if self.ba_id:
            payment_source = {"token": {"id": self.ba_id, "type": "BILLING_AGREEMENT"}}
            return payment_source

        context = self.build_context()
        paypal = {
            "experience_context": context,
        }

        if self.vault_id:
            paypal["vault_id"] = self.vault_id
        elif self.vault_v3:
            paypal["attributes"] = {
                "vault": {
                    "store_in_vault": "ON_SUCCESS",
                    "usage_type": self.vault_v3,
                }
            }

        payment_source = {"paypal": paypal}
        return payment_source

    def create(self):
        """Create the order with the /v2/checkout/orders API.

        Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_create
        """
        endpoint = build_endpoint("/v2/checkout/orders")
        headers = self.build_headers()

        purchase_units = [self.build_purchase_unit()]
        payment_source = self.build_payment_source()
        data = {
            "intent": self.intent,
            "purchase_units": purchase_units,
            "payment_source": payment_source,
        }

        response = requests.post(
            endpoint,
            headers=headers,
            json=data,
        )
        self.formatted["create-order"] = format_request_and_response(response)
        response_dict = {
            "formatted": self.formatted,
            "authHeader": self.auth_header,
        }
        try:
            order_id = response.json()["id"]
        except Exception as exc:
            current_app.logger.error(f"Encountered exception unpacking order ID: {exc}")
            return response_dict

        response_dict["orderId"] = order_id
        return response_dict

    def capture(self):
        """Capture the order.

        Docs: https://developer.paypal.com/docs/api/orders/v2/#orders_capture
        """
        if not self.order_id:
            raise ValueError

        if self.intent == "AUTHORIZE":
            return self.auth_and_capture()

        endpoint = build_endpoint(f"/v2/checkout/orders/{self.order_id}/capture")
        headers = self.build_headers()

        data = {}

        payment_instruction = self.build_payment_instruction(for_call="capture")
        if payment_instruction:
            data["payment_instruction"] = payment_instruction

        response = requests.post(endpoint, headers=headers, json=data)
        self.formatted["capture-order"] = format_request_and_response(response)
        response_dict = {
            "formatted": self.formatted,
        }

        response_dict["authHeader"] = self.auth_header
        return response_dict

    def authorize(self):
        endpoint = build_endpoint(f"/v2/checkout/orders/{self.order_id}/authorize")

        headers = self.build_headers()

        response = requests.post(endpoint, headers=headers)
        self.formatted["authorize-order"] = format_request_and_response(response)

        return response

    def capture_authorization(self):
        endpoint = build_endpoint(f"/v2/payments/authorizations/{self.auth_id}/capture")

        headers = self.build_headers()

        data = dict()
        payment_instruction = self.build_payment_instruction(for_call="capture")
        if payment_instruction:
            data["payment_instruction"] = payment_instruction

        response = requests.post(endpoint, headers=headers, json=data)
        self.formatted["capture-authorization"] = format_request_and_response(response)

        return response

    def auth_and_capture(self):
        auth_response = self.authorize()
        response_dict = {"formatted": self.formatted, "authHeader": self.auth_header}
        try:
            self.auth_id = auth_response.json()["purchase_units"][0]["payments"][
                "authorizations"
            ][0]["id"]
        except (TypeError, IndexError) as exc:
            current_app.logger.error(
                f"Error accessing authorization ID from response: {exc}"
            )
            return response_dict

        self.capture_authorization()
        response_dict["formatted"] = self.formatted

        return response_dict

    def status(self):
        if self.order_id is None:
            raise ValueError

        endpoint = build_endpoint(f"/v2/checkout/orders/{self.order_id}")
        headers = self.build_headers()

        response = requests.get(endpoint, headers=headers)
        self.formatted["order-status"] = format_request_and_response(response)

        return {"formatted": self.formatted}


@bp.route("/create", methods=("POST",))
def create_order():
    data = request.get_json()
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.debug(
        f"Creating an order with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    order = Order(**data)
    resp = order.create()

    current_app.logger.debug(f"Create order response: {json.dumps(resp, indent=2)}")
    return jsonify(resp)


@bp.route("/capture/<order_id>", methods=("POST",))
def capture_order(order_id):
    data = request.get_json()
    data["order-id"] = order_id
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.debug(
        f"Capturing an order with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    order = Order(**data)
    resp = order.capture()

    current_app.logger.debug(f"Capture order response: {json.dumps(resp, indent=2)}")
    return jsonify(resp)


@bp.route("/status/<order_id>", methods=("POST",))
def order_status(order_id):
    data = request.get_json()
    data["order-id"] = order_id
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.debug(
        f"Getting the status of an order with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    order = Order(**data)
    resp = order.status()

    current_app.logger.debug(f"Get order status response: {json.dumps(resp, indent=2)}")
    return jsonify(resp)
