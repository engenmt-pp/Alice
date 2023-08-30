from multiprocessing import cpu_count

proc_name = "alice"
workers = 2 * cpu_count() + 1
bind = "0.0.0.0:8000"
wsgi_app = "app:app"
# daemon = True
accesslog = "access_log.log"
access_log_format = '{"date_time": "%(t)s", "remote_address": "%(h)s", "referer": "%(f)s", "method": "%(m)s", "url_path": "%(U)s", "status": "%(s)s", "user_agent": "%(a)s", "request_time_in_seconds": "%(L)s"}'
# Docs: https://docs.gunicorn.org/en/stable/settings.html#access-log-format
# t -> date of the request (e.g., [30/Aug/2023:13:44:38 -0400])
# h -> remote address (e.g., 127.0.0.1)
# f -> referer (e.g., /checkout/)
# m -> method (e.g., POST)
# U -> URL path without query string (e.g., /API/orders/)
# s -> status (e.g., 200)
# a -> user agent (e.g., Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/116.0)
# L -> request time in decimal seconds
