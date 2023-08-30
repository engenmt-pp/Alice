proc_name = "alice"
workers = 1
bind = "0.0.0.0:8000"
wsgi_app = "app:app"
# daemon = True
accesslog = "access_log.log"
