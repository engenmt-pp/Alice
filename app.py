#!/usr/bin/env python3

from config import PartnerOneConfig, MerchantOneConfig
from src import create_app


if __name__ == "__main__":

    app = create_app()

    app.config.from_object(PartnerOneConfig)
    # app.config.from_object(MerchantOneConfig)

    # from partner_specific_config import PartnerMerchantConfig
    # app.config.from_object(PartnerMerchantConfig)

    from partner_specific_config import MerchantAppConfig

    app.config.from_object(MerchantAppConfig)

    app.logger.info(f"Partner ID: {app.config['PARTNER_ID']}")
    app.logger.info(f"Merchant ID: {app.config['MERCHANT_ID']}")

    app.run(host="127.0.0.1", port=5000)
