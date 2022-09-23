#!/usr/bin/env python3

from config import SandboxConfig, PartnerOneConfig, MerchantPPGFConfig
from src import create_app


if __name__ == "__main__":

    app = create_app()

    testing = True  # Enables debug-level logging
    # testing = False  # Disables debug-level logging
    if testing:
        # from partner_specific_config import PartnerInderConfig

        app.config.from_object(PartnerOneConfig)
        app.config.from_object(MerchantPPGFConfig)
    else:
        app.config.from_object(SandboxConfig)

    app.logger.info(f"Partner ID: {app.config['PARTNER_ID']}")
    app.logger.info(f"Merchant ID: {app.config['MERCHANT_ID']}")
    app.run(host="127.0.0.1", port=5000)
