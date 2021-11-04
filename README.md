# A Partner Integration --- An example in Python

Let's set up a PPCP Connected Path integration in the sandbox using Python 3.9.6. This project is **purely** for teaching purposes. Coding best practices are frequently forgone here in favor of simplicity.  

## Sign-up

To begin acting as a Partner, we need an access token. To request an access token, we need the `client_id` and `secret` for our Partner. Below, these are saved in the `PARTNER_CLIENT_ID` and `PARTNER_SECRET` variables, which we import from `my_secrets.py`:
```python
>>> from my_secrets import PARTNER_CLIENT_ID, PARTNER_SECRET 
```

We'll send our API requests using the `requests` library, and handle the dictionary-to-string conversions with the `json` library where needed. To generate an access token, we'll send a POST request to the `v1/oauth2/token` endpoint with our `client_id` and `secret`:

```python
>>> import json, requests
>>> endpoint = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
>>> response = requests.post(
...     endpoint,
...     headers={"Content-Type": "application/json", "Accept-Language": "en_US"},
...     data={"grant_type": "client_credentials"},
...     auth=(client_id, secret),
... )
...
>>> response_dict = response.json() # Extracts the dictionary from the response.
>>> print(json.dumps(response_dict, indent=2)) # Prints the dictionary nicely formatted.
{
  "scope": "https://uri.paypal.com/services/customer/partner-referrals/readwrite https://uri.paypal.com/services/invoicing https://uri.paypal.com/services/vault/payment-tokens/read https://uri.paypal.com/services/disputes/read-buyer https://uri.paypal.com/services/payments/realtimepayment https://uri.paypal.com/services/customer/onboarding/user https://api.paypal.com/v1/vault/credit-card https://api.paypal.com/v1/payments/.* https://uri.paypal.com/services/payments/referenced-payouts-items/readwrite https://uri.paypal.com/services/reporting/search/read https://uri.paypal.com/services/customer/partner https://uri.paypal.com/services/vault/payment-tokens/readwrite https://uri.paypal.com/services/customer/merchant-integrations/read https://uri.paypal.com/services/applications/webhooks https://uri.paypal.com/services/disputes/update-seller https://uri.paypal.com/services/payments/payment/authcapture openid https://uri.paypal.com/services/disputes/read-seller https://uri.paypal.com/services/payments/refund https://uri.paypal.com/services/risk/raas/transaction-context https://uri.paypal.com/services/partners/merchant-accounts/readwrite https://uri.paypal.com/services/identity/grantdelegation https://uri.paypal.com/services/customer/onboarding/account https://uri.paypal.com/payments/payouts https://uri.paypal.com/services/customer/onboarding/sessions https://api.paypal.com/v1/vault/credit-card/.* https://uri.paypal.com/services/subscriptions",
  "access_token": "A21AAIVFhh3qBLX6wt_md89b6CVIFnKnQ8qDp9wrJn7wSyS9iC7MzIl_1Hw6LtEngDWnKyJD4GXPFthPyKDsbHMrNiTDmtCbA",
  "token_type": "Bearer",
  "app_id": "APP-80W284485P519543T",
  "expires_in": 32103,
  "nonce": "2021-10-22T16:42:45ZeDCE7H9OEkGizRgxFa9Wj0mdwArOkP3PtZJWmgUTj8k"
}
```
Within the response dictionary is the `access_token` as well as the number of seconds for which the access token is valid in `expires_in`. In this case, the access token is valid for 32,103 more seconds. For simplicity, we'll just use the access token, and bundle this process into a function. We'll set the default values of `client_id` and `secret` to be `PARTNER_CLIENT_ID` and `PARTNER_SECRET`, respectively.

```python
def request_access_token(client_id, secret):
    endpoint = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    response = requests.post(
        endpoint,
        headers={"Content-Type": "application/json", "Accept-Language": "en_US"},
        data={"grant_type": "client_credentials"},
        auth=(client_id, secret),
    )
    response_dict = response.json()
    return response_dict["access_token"]
```
> `src/api.py`
---
<br>

Each of our subsequent API requests will include a header with the `Content-Type`, which will be `application/json`, and an `Authorization`, which will be the string `Bearer {access_token}`, where `{access_token}` will be replaced with the access token obtained above. We write a small function that will build these headers with a fresh access token on each call. Note that in practice, we should reuse access tokens whenever possible to help avoid rate limits on API calls. 
```python
def build_headers(client_id=PARTNER_CLIENT_ID, secret=PARTNER_SECRET):
    access_token = request_access_token(client_id, secret)
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
```
> `src/api.py`
---
<br>

With a (process to generate an) access token in hand, we'll request a sign-up link for each of our prospective merchants to use. We'll use the v2 API, but v1 can be used as well. To generate a sign-up link, we need to 
- assign each merchant a distinct `tracking_id` (`5675309` in this case),
- choose which features the merchant will have access to (`PAYMENT`, `REFUND`, `PARTNER_FEE`, and `DELAY_FUNDS_DISBURSEMENT` in this case),
- decide which product to sign the merchant up for (`PPCP` in this case),
- and provide a `return_url` that the merchant will be redirected to upon completing the sign-up process (`paypal.com` in this case).

```python
>>> tracking_id = "8675309"
>>> return_url = "paypal.com"
>>> data = {
...     "tracking_id": tracking_id,
...     "operations": [
...         {
...             "operation": "API_INTEGRATION",
...             "api_integration_preference": {
...                 "rest_api_integration": {
...                     "integration_method": "PAYPAL",
...                     "integration_type": "THIRD_PARTY",
...                     "third_party_details": {
...                         "features": [
...                             "PAYMENT",
...                             "REFUND",
...                             "PARTNER_FEE",
...                             "DELAY_FUNDS_DISBURSEMENT",
...                         ]
...                     },
...                 }
...             },
...         }
...     ],
...     "products": ["PPCP"],
...     "legal_consents": [{"type": "SHARE_DATA_CONSENT", "granted": True}],
...     "partner_config_override": {"return_url": return_url},
... }
>>> headers = build_headers()
>>> response = requests.post(
...     "https://api-m.sandbox.paypal.com/v2/customer/partner-referrals",
...     headers=headers,
...     data=json.dumps(data),
... )
>>> response_dict = response.json()
>>> print(json.dumps(response_dict, indent=2))
{
  "links": [
    {
      "href": "https://api.sandbox.paypal.com/v2/customer/partner-referrals/NjY1ZDZiM2EtYmQ4Yi00ZjJmLWJmYzItNDM1OTU2NmM4ZmRlbUFjbEtKRHBVUXVWc2ZTYjJBZDRlbHpVRFo4UE5ZbjZQVlZSc2JpS2N6Yz12Mg==",        
      "rel": "self",
      "method": "GET",
      "description": "Read Referral Data shared by the Caller."
    },
    {
      "href": "https://www.sandbox.paypal.com/bizsignup/partner/entry?referralToken=NjY1ZDZiM2EtYmQ4Yi00ZjJmLWJmYzItNDM1OTU2NmM4ZmRlbUFjbEtKRHBVUXVWc2ZTYjJBZDRlbHpVRFo4UE5ZbjZQVlZSc2JpS2N6Yz12Mg==",
      "rel": "action_url",
      "method": "GET",
      "description": "Target WEB REDIRECT URL for the next action. Customer should be redirected to this URL in the browser."
    }
  ]
}
```

The second link, the one with labeled as the `action_url`, is the link that we should direct merchants to. We can loop through the response dictionary to extract the link:
```python
>>> for link in response_dict["links"]:
...     if link["rel"] == "action_url":
...         print(link["href"])
...
"https://www.sandbox.paypal.com/bizsignup/partner/entry?referralToken=NjY1ZDZiM2EtYmQ4Yi00ZjJmLWJmYzItNDM1OTU2NmM4ZmRlbUFjbEtKRHBVUXVWc2ZTYjJBZDRlbHpVRFo4UE5ZbjZQVlZSc2JpS2N6Yz12Mg=="
```

We can package all of this into a function that takes the `tracking_id` and `return_url` as inputs and returns the sign-up link. For convenience, we'll set the default `return_url` to be `"paypal.com"`.
```python
def generate_sign_up_link(tracking_id, return_url="paypal.com"):
    data = {
        "tracking_id": tracking_id,
        "operations": [
            {
                "operation": "API_INTEGRATION",
                "api_integration_preference": {
                    "rest_api_integration": {
                        "integration_method": "PAYPAL",
                        "integration_type": "THIRD_PARTY",
                        "third_party_details": {
                            "features": [
                                "PAYMENT",
                                "REFUND",
                                "PARTNER_FEE",
                                "DELAY_FUNDS_DISBURSEMENT",
                            ]
                        },
                    }
                },
            }
        ],
        "products": ["PPCP"],
        "legal_consents": [{"type": "SHARE_DATA_CONSENT", "granted": True}],
        "partner_config_override": {"return_url": return_url},
    }

    response = requests.post(
        "https://api-m.sandbox.paypal.com/v2/customer/partner-referrals",
        headers=build_headers(),
        data=json.dumps(data),
    )
    response_dict = response.json()

    for link in response_dict["links"]:
        if link["rel"] == "action_url":
            return link["href"]
    else:
        # If we're here, no `action_url` was found!
        raise Exception("No action url found!")
```
> `src/api.py`
---
<br>

When a merchant has begun the sign-up process, you can track their progress with a GET request to `/v1/customer/partners/{partner_id}/merchant-integrations/{merchant_id}`, where `partner_id` and `merchant_id` are the "PayPal Merchant ID" for the partner and merchant, respectively. We import `PARTNER_ID` from our `my_secrets` file. The merchant's `merchant_id` can be discovered using a GET request to `/v1/customer/partners/{partner_id}/merchant-integrations?tracking_id={tracking_id}`:

```python
from my_secrets import PARTNER_ID

def get_merchant_id(tracking_id):
    endpoint = f"https://api-m.sandbox.paypal.com/v1/customer/partners/{PARTNER_ID}/merchant-integrations?tracking_id={tracking_id}"

    response = requests.get(endpoint, headers=headers)

    response_dict = response.json()
    return response_dict["merchant_id"]

def get_status(merchant_id):
    endpoint = f"https://api-m.sandbox.paypal.com/v1/customer/partners/{PARTNER_ID}/merchant-integrations/{merchant_id}"

    response = requests.get(endpoint, headers=headers)

    response_dict = response.json()
    return response_dict
```
> `src/api.py`
---
<br>

## A Sign-up Webpage

We'll now combine all of this and display it to a prospective merchant. For this example, we'll use the `flask` Python library, but it's not vitally important that you know the details of `flask`. In our `src/` directory, we create a barebones [initialization file](https://flask.palletsprojects.com/en/2.0.x/tutorial/factory/):

```python
import os
from flask import Flask

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY="dev")

    os.makedirs(app.instance_path, exist_ok=True)

    from . import partner

    app.register_blueprint(partner.bp)

    return app
```
> `src/__init__.py`
---
<br>

The sign-up webpage will be based on the template `src/templates/sign_up.html`, which can will contain two links: one for signing up and one for navigating to the status. The best practice for the sign-up link is to open it in a mini-browser, as described [here](https://developer.paypal.com/docs/multiparty/seller-onboarding/before-payment/), so this is how we have implemented it. We'll also add a [blueprint](https://flask.palletsprojects.com/en/2.0.x/blueprints/) to a new file `src/partner.py` and [decorate](https://www.python.org/dev/peps/pep-0318/) its methods to allow them to be accessed through various URLs:

```python
import json

from .api import generate_sign_up_link, get_merchant_id, get_status
from flask import Blueprint, render_template, url_for

bp = Blueprint(
    "partner", 
    __name__, 
    url_prefix="/partner" # Routes on this page will be prefixed with /partner
) 


@bp.route("/sign-up")
def sign_up(tracking_id="8675309"):
    sign_up_link = generate_sign_up_link(tracking_id)

    # Get the URL for the corresponding status page
    tracking_url = url_for("partner.status", tracking_id=tracking_id)

    return render_template(
        "sign_up.html", sign_up_link=sign_up_link, tracking_url=tracking_url
    )


@bp.route("/status/<tracking_id>")
def status(tracking_id):
    merchant_id = get_merchant_id(tracking_id)
    status = get_status(merchant_id)
    status_text = json.dumps(status, indent=2)
    return render_template("status.html", status=status_text)

```
> `src/partner.py`
---
<br>

With the above `bp.route` decorators in place, navigating to `http://127.0.0.1:5000/partner/sign-up` will present a simple page that includes our sign-up link and a link to a sign-up status page. These pages are built from two simple templates, `templates/sign_up.html` and `templates/status.html`. Finally, we can run our webserver after setting our app name and environment: 
```bash
$ export FLASK_APP=src
$ export FLASK_ENV=development
$ python -m flask run
 * Serving Flask app 'flaskr' (lazy loading)
 * Environment: development
 * Debug mode: on
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 101-820-955
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

Then, we can navigate to `http://127.0.0.1:5000/partner/sign-up`, click the sign-up link, and sign in with a Sandbox merchant's credentials. Once you are finished signing up, click the status link. 


Note: In the templates, [jinja](https://jinja.palletsprojects.com/en/3.0.x/) formatting is used. Within the double curly braces, Python code is executed with the supplied variables. For example, the snippet `{{ status }}` in `status.html` is replaced with the `status_text` properly in `render_template("status.html", status=status_text)`. We'll continue to use this templating throughout the walkthrough.

## Processing Orders

It's time to process some orders! In many cases, PayPal's Javascript SDK alone can be used to create orders and capture their funds, but the Javascript SDK alone does not suffice for PPCP Connected Path integrations. In addition to the Javascript SDK, we'll also use the [Orders API v2](https://developer.paypal.com/docs/api/orders/v2/) to create and capture our orders. 

Before we begin, we'll need the Partner's build notation (BN) code (also called their ["PayPal-Partner-Attribution-Id"](https://developer.paypal.com/docs/api/orders/v2/?mark=partner-attribution#orders-create-header-parameters)) and the Merchant's ID (also called the Merchant's "merchant ID" or the `payee_merchant_id`.) The BN code is typically assigned to a partner through Salesforce, but we'll pick ours arbitrarily and hardcode both it and the `payee_merchant_id`.

For our simple example, we'll integrate [Smart Payment Buttons](https://developer.paypal.com/docs/checkout/) onto our website. To begin, we'll create checkout page for a single hardcoded product, an apple pie. In a new file `src/store.py`, we'll include some standard imports and a route for hosting our checkout page: 

```python
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
        payee_merchant_id=PAYEE_MERCHANT_ID,
        bn_code=MERCHANT_BN_CODE,
    )
```
> `src/store.py`
---
<br>

Additionally, we'll need to register the above blueprint in our `__init__.py` file as we did with `store.py`. Our HTML template will be fairly barebones, including just some product information and our Smart Payment buttons:
```html
<article>
  <body>
    
    <!-- Information about the product -->
    <h1>Product Page</h1>
    <p>Product name: {{ product['name'] }}</p>
    <p>Price: ${{ product['price'] }}</p>
    <p>Description: {{ product['description'] }}</p> 

    <!-- Empty (for now) button container -->
    <div class="smart-button-container", id="smart-button-container">
      <div style="text-align: center;">
        <div id="paypal-button-container"></div>
      </div>
    </div>
    
    <!-- Import PayPal Javascript SDK with Partner's Client Id and the Merchant's Merchant ID -->
    <script src="https://www.paypal.com/sdk/js?client-id={{ partner_client_id }}&merchant-id={{ payee_merchant_id }}&currency=USD&intent=capture" data-partner-attribution-id="{{ bn_code }}"></script>

    <script>
      function initPayPalButton() {
        paypal.Buttons({
          createOrder: function (data, actions) {
            return fetch('/api/create-order', {
              headers: {'Content-Type': 'application/json'},
              method: 'POST',
              body: JSON.stringify({
                price: "{{ product['price'] }}", 
                payee_merchant_id: "{{ payee_merchant_id }}", 
                bn_code: "{{ bn_code }}"
              })
            }).then(function(res) {
              return res.json();
            }).then(function(data) {
              return data.id;
            })
          },
          onApprove: function(data, actions) {
            return fetch('/api/capture-order', {
              headers: {'Content-Type': 'application/json'},
              method: 'POST',
              body: JSON.stringify({orderId: data.orderID})
            }).then(function(res) {
              return res.json();
            }).then(function(captureData) {
              // Your server response structure and key names are what you choose
              if (captureData.error === 'INSTRUMENT_DECLINED') {
                return actions.restart();
              } else {
                window.location.replace("/store/order-details/" + data.orderID);
              }
            })  
          }
        }).render('#paypal-button-container');
      }
      initPayPalButton();
    </script>
  </body>
</article>
```
> `src/templates/checkout.html`
---
<br>

The kernel of the checkout page lies in the `initPayPalButton` call with the functions passed into the `createOrder` and `onApprove` keys. Where simpler contexts allow for the Javascript SDK itself to create and capture the order, PPCP requires our server to make the API calls, so we begin by submitting a POST request to our server through `/api/create-order` containing the price, Payee's (Merchant's) Merchant ID, and the Partner's BN code. 

To consume this API call, we'll create a new function in `api.py` that calls out to the [Orders v2 API](https://developer.paypal.com/docs/api/orders/v2/#orders_create). We can extract the contents of the request using the [`flask.request` object](https://flask.palletsprojects.com/en/2.0.x/api/#flask.request). In addition to the usual authentication headers, we also need to add the Partner's BN code under the key `PayPal-Partner-Attribution-Id` for PayPal to properly associate the order with the partner. Moreover, the order will only be associated with the Merchant if the Merchant's "Merchant ID" is passed into the API request in the `payee` field.

```python
@bp.route("/create-order", methods=("POST",))
def create_order():
    endpoint = "https://api-m.sandbox.paypal.com/v2/checkout/orders"

    headers = build_headers()
    headers["PayPal-Partner-Attribution-Id"] = request.json["bn_code"]

    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "payee": {"merchant_id": request.json["payee_merchant_id"]},
                "amount": {
                    "currency_code": "USD",
                    "value": request.json["price"],
                }
            }
        ],
    }

    response = requests.post(endpoint, headers=headers, data=json.dumps(data))
    response_dict = response.json()
    return jsonify(response_dict)
```
> `src/api.py`
---
<br>

The other piece of the puzzle is order capture, which we accomplish in a manner similar to order creation, but with the [Capture Orders v2 API](https://developer.paypal.com/docs/api/orders/v2/#orders_capture). In this case, the client-side SDK needs only to send the order ID to `/api/capture-order`, and our server-side code will take care of the API call:

```python
@bp.route("/capture-order", methods=("POST",))
def capture_order():
    endpoint = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{request.json['orderId']}/capture"

    headers = build_headers()

    response = requests.post(endpoint, headers=headers)
    response_dict = response.json()
    return jsonify(response_dict)
```
> `src/api.py`
---
<br>

Finally, we'll set up a simple order details page to redirect customers to after their successful purchase. To get the order details, we'll use the [Get Orders v2 API](https://developer.paypal.com/docs/api/orders/v2/#orders_get):
```python
def get_order_details(order_id):
    endpoint = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}"

    headers = build_headers()

    response = requests.get(endpoint, headers=headers)
    response_dict = response.json()
    return response_dict
```
> `src/api.py`
---
<br>

Our store page will be located at `/store/order-details/{order_id}`, and we'll reuse our `status.html` template from before.
```python
@bp.route("/order-details/<order_id>")
def order_details(order_id):
    order_details_dict = get_order_details(order_id)
    order_details_str = json.dumps(order_details_dict, indent=2)
    return render_template("status.html", status=order_details_str)

```
> `src/store.py`
---
<br>

With these store pages and API endpoints set up, we can navigate to [127.0.0.1:5000/store/checkout](127.0.0.1:5000/store/checkout) and be presented with our simple checkout page. Upon payment completion, we are appropriately rerouted to our order details page.