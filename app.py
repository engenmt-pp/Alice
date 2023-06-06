#!/usr/bin/env python3.10

from src import create_app

app = create_app()

from config import PartnerOneConfig, MerchantOneConfig

app.config.from_object(PartnerOneConfig)
app.config.from_object(MerchantOneConfig)

# from partner_specific_config import VaultV3Config
# app.config.from_object(VaultV3Config)

if __name__ == "__main__":
    from logging.config import dictConfig

    dictConfig({"version": 1, "root": {"level": "INFO"}})
    app.run(host="127.0.0.1", port=5000, debug=True)
