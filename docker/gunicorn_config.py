import multiprocessing
from os import getenv
bind = '127.0.0.1:8001'

workers = multiprocessing.cpu_count() * 3
graceful_timeout = 60
timeout = 90
threads = multiprocessing.cpu_count() * 3

pidfile = '/var/run/gunicorn.pid'

errorlog = '/var/log/gunicorn/gunicorn-error.log'
loglevel = 'critical'

# Read the DEBUG setting from env var
try:
    if getenv('DOCKER_SAL_DEBUG').lower() == 'true':
        accesslog = '/var/log/gunicorn/gunicorn-access.log'
        loglevel = 'info'
except Exception:
    pass

# Protect against memory leaks by restarting each worker every 1000
# requests, with a randomized jitter of 0-50 requests.
max_requests = 1000
max_requests_jitter = 50
worker_class = 'gevent'
