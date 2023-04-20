#!/usr/bin/env python3.10

from config import PartnerOneConfig, MerchantOneConfig
from partner_specific_config import MerchantCCConfig

from src import create_app

app = create_app()

app.config.from_object(PartnerOneConfig)
app.config.from_object(MerchantCCConfig)

if __name__ == "__main__":
    from logging.config import dictConfig

    dictConfig({"version": 1, "root": {"level": "INFO"}})
    app.run(host="127.0.0.1", port=5000)
