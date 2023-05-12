#!/usr/bin/env python3

import os
from flask import Flask

from logging.config import dictConfig


def create_app():
    dictConfig({"version": 1, "root": {"level": "DEBUG"}})

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY="dev")
    app.jinja_env.globals.update(
        zip=zip
    )  # Allows for the use of `zip` in Jinja2 formatting.

    os.makedirs(app.instance_path, exist_ok=True)

    from . import api, onboarding, store, store_form, reports
    from . import store_merchant
    from . import statuses

    app.register_blueprint(api.bp)
    app.register_blueprint(reports.bp)

    app.register_blueprint(store.bp)
    app.register_blueprint(store_form.bp)
    app.register_blueprint(onboarding.bp)
    app.register_blueprint(statuses.bp)
    app.add_url_rule("/", endpoint="store_form.checkout_branded")

    app.register_blueprint(store_merchant.bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
