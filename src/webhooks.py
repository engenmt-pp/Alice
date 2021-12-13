import json

# import requests
# from .my_secrets import PARTNER_CLIENT_ID, PARTNER_ID, PARTNER_SECRET

from flask import Blueprint, request, jsonify

bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")


@bp.route("/", methods=("POST",))
def listener():
    """
    Listen to:
    - *
    """
    print(f"Webhook received:\n{json.dumps(request.json, indent=2)}")
    return "", 204


if __name__ == "__main__":
    pass
