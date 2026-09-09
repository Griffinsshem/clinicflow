import os

bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
threads = 2
worker_class = "gthread"
max_requests = 1000
max_requests_jitter = 10
timeout = 25
graceful_timeout = 20
keepalive = 65
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s "%(m)s %(U)s" %(s)s %(b)s %(L)ss'
