# Alice - A PPCP Testing Tool

Alice is a tool for testing PayPal Commerce Platform (PPCP) features and functionality.

## Run Alice locally

### Set up `.env` file

To run Alice locally, first load partner and merchant credentials into a file named `.env` in the following format:
```
PARTNER_CLIENT_ID = AWjz...
PARTNER_SECRET = ECLx...
PARTNER_ID = UB8L...
PARTNER_BN_CODE = FLA...

MERCHANT_ID = NY9...
WEBHOOK_ID = 2SY...
```

### Install python and project dependencies

Install python. Then run...

```bash
python3 -m pip install -r requirements.txt
```

### Run the app

```bash
python3 app.py
```