#!/usr/bin/env python3

from config import SandboxConfig, TestingConfig, PartnerOneConfig, MerchantOneConfig
from partner_specific_config import PartnerSpecificConfig
from src import create_app


if __name__ == "__main__":

    app = create_app()

    testing = True
    # testing = False
    if testing:
        from partner_specific_config import PartnerInderConfig, MerchantThreeConfig

        app.config.from_object(PartnerOneConfig)
        app.config.from_object(MerchantThreeConfig)
    else:
        app.config.from_object(SandboxConfig)

    app.logger.info(f"Partner ID: {app.config['PARTNER_ID']}")
    app.logger.info(f"Merchant ID: {app.config['MERCHANT_ID']}")
    app.run(host="127.0.0.1", port=5000)
