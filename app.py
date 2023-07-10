#!/usr/bin/env python3.10

from src import create_app

app = create_app()

from config import PartnerOneConfig, MerchantOneConfig

app.config.from_object(PartnerOneConfig)
app.config.from_object(MerchantOneConfig)

if __name__ == "__main__":
    from logging.config import dictConfig

    dictConfig({"version": 1, "root": {"level": "INFO"}})

    app.config["favicon"] = "♣️"  # Club emoji. Devs are part of the club!

    app.run(host="127.0.0.1", port=5000, debug=True)
else:
    app.config["favicon"] = "♠️"  # Spade emoji for the rest of us.
