import json

from flask import Blueprint, current_app, render_template, url_for
from .api.charities import get_charities

bp = Blueprint("charities", __name__, url_prefix="/charities")


@bp.route("/")
def charities_list():
    charities = get_charities()
    charities_str = json.dumps(charities.json(), indent=2)
    return render_template("status.html", status=charities_str, contexts=[])
