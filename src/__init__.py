#!/usr/bin/env python3

import os
from flask import Flask

from logging.config import dictConfig


def create_app():
    dictConfig({"version": 1, "root": {"level": "ERROR"}})

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY="dev")

    os.makedirs(app.instance_path, exist_ok=True)

    from . import api, routes  # , statuses, onboarding, checkout

    app.register_blueprint(api.bp)

    app.register_blueprint(routes.bp)
    # app.register_blueprint(checkout.bp)
    # app.register_blueprint(onboarding.bp)
    # app.register_blueprint(statuses.bp)

    return app
