from flask import Blueprint

bp = Blueprint("api", __name__, url_prefix="/api")

from . import orders, orders_form, referrals, webhooks

from . import orders_merchant

bp.register_blueprint(orders.bp)
bp.register_blueprint(orders_form.bp)
bp.register_blueprint(referrals.bp)
bp.register_blueprint(webhooks.bp)

bp.register_blueprint(orders_merchant.bp)
