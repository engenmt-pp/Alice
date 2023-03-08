#!/usr/bin/env python3.10

from config import PartnerOneConfig, MerchantOneConfig

from src import create_app

app = create_app()

app.config.from_object(PartnerOneConfig)
app.config.from_object(MerchantOneConfig)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
