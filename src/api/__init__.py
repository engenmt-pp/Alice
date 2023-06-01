from flask import Blueprint

bp = Blueprint("api", __name__, url_prefix="/api")

from . import (
    identity,
    orders,
    partner,
    webhooks,
)

bp.register_blueprint(identity.bp)
bp.register_blueprint(orders.bp)
bp.register_blueprint(partner.bp)
bp.register_blueprint(webhooks.bp)
