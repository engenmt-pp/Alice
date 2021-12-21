import json

from flask import Blueprint, request

bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")


@bp.route("/", methods=("POST",))
def listener():
    webhook_dict = request.json
    print(f"Webhook received:\n{json.dumps(webhook_dict, indent=2)}")
    return "", 204
