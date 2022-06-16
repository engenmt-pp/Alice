from flask import Blueprint

bp = Blueprint("api", __name__, url_prefix="/api")

from . import orders, referrals, webhooks

bp.register_blueprint(orders.bp)
bp.register_blueprint(referrals.bp)
bp.register_blueprint(webhooks.bp)
