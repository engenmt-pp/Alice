#!/usr/bin/env python3

from config import DevelopmentConfig, TestingConfig
from partner_specific_config import PartnerSpecificConfig
from src import create_app


if __name__ == "__main__":

    app = create_app()

    testing = True
    # testing = False
    if testing:
        # app.config.from_object(PartnerSpecificConfig)  # Enables debug-level logging
        app.config.from_object(TestingConfig)  # Enables debug-level logging
    else:
        app.config.from_object(DevelopmentConfig)  # Disables debug-level logging

    app.run(host="127.0.0.1", port=5000)
