from flask import Blueprint

bp = Blueprint("api", __name__, url_prefix="/api")

from . import billing_agreements, captures, identity, orders, partner, vault, webhooks

bp.register_blueprint(billing_agreements.bp)
bp.register_blueprint(captures.bp)
bp.register_blueprint(identity.bp)
bp.register_blueprint(orders.bp)
bp.register_blueprint(partner.bp)
bp.register_blueprint(vault.bp)
bp.register_blueprint(webhooks.bp)
