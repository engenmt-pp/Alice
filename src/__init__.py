#!/usr/bin/env python3

import os
from flask import Flask

from logging.config import dictConfig


def create_app():
    dictConfig({"version": 1, "root": {"level": "ERROR"}})

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY="dev")
    app.jinja_env.globals.update(
        zip=zip
    )  # Allows for the use of `zip` in Jinja2 formatting.

    os.makedirs(app.instance_path, exist_ok=True)

    from . import api, statuses, onboarding, checkout

    app.register_blueprint(api.bp)

    app.register_blueprint(checkout.bp)
    app.register_blueprint(onboarding.bp)
    app.register_blueprint(statuses.bp)
    app.add_url_rule("/", endpoint="checkout.checkout")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
