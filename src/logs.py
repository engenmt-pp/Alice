import logging


class FilterNoStatic(logging.Filter):
    def filter(self, record):
        return "/static/" not in record.args["U"]
