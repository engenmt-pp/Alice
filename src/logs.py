# from flask import has_request_context, request
# from flask.logging import default_handler
import json
import logging


# from gunicorn.glogging import Logger


# class CustomGunicornLogger(Logger):
#     def access(self, resp, req, environ, request_time):
#         if "/static" not in req.path:
#             super().access(resp, req, environ, request_time)


# class RequestFormatter(logging.Formatter):
#     def format(self, record):
#         if has_request_context():
#             record.url = request.url
#             record.remote_addr = request.remote_addr
#         else:
#             record.url = None
#             record.remote_addr = None

#         return super().format(record)
# formatter = RequestFormatter(
#     "[%(asctime)s] %(remote_addr)s requested %(url)s\n"
#     "%(levelname)s in %(module)s: %(message)s"
# )
# default_handler.setFormatter(formatter)
# mail_handler.setFormatter(formatter)


class FilterNoStatic(logging.Filter):
    def filter(self, record):
        # print(record.args["U"])
        return "/static/" not in record.args["U"]  # URL
        # for key, value in sorted(record.args.items()):
        #     print(f"\t{key}: {value}")
        # print(f"{record.getMessage()=}")
        # body = record.args.get("{wsgi.input}e")
        # if body:
        #     body = body.read()
        # if body:
        #     print(f"body = {body}")


def get_logging_config_prod():
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "NoStatic": {
                "()": FilterNoStatic,
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.handlers.FileHandler",
                "filename": "log.log",
                "mode": "a",
                "encoding": "utf-8",
                "filters": ["NoStatic"],
            },
        },
        "loggers": {"gunicorn.access": {"handlers": ["file"]}},
        "root": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
        },
    }
    # return {
    #     "version": 1,
    #     "root": {"level": "DEBUG"},
    #     "disable_existing_loggers": False,
    #     "filters": {
    #         "NoStatic": {
    #             "()": FilterNoStatic,
    #         }
    #     },
    #     "loggers": {
    #         "gunicorn.access": {
    #             #         "propagate": True,
    #             "filters": ["NoStatic"],
    #         },
    #     },
    # }
