#!/usr/bin/env python3.10
import logging
from logging.config import dictConfig

from src import create_app
from config import PartnerOneConfig, MerchantOneConfig, ManagedPathPartnerConfigOne

from src.logs import FilterNoStatic

app = create_app()
app.config.from_object(PartnerOneConfig)
app.config.from_object(MerchantOneConfig)
app.config.from_object(ManagedPathPartnerConfigOne)


if __name__ == "__main__":
    dictConfig(
        {
            "version": 1,
            "root": {"level": "DEBUG"},
        }
    )

    app.config["favicon"] = "♣️"  # Club emoji. Devs are part of the club!

    app.run(host="127.0.0.1", port=8000, debug=True)
else:
    logger = logging.getLogger("gunicorn.access")
    logger.addFilter(FilterNoStatic())
    app.config["favicon"] = "♠️"  # Spade emoji for the rest of us.
