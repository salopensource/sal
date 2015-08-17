import multiprocessing
from os import getenv
bind = '127.0.0.1:8001'
workers = multiprocessing.cpu_count() * 2 + 1
# Read the DEBUG setting from env var
try:
    if getenv('DOCKER_SAL_DEBUG').lower() == 'true':
        errorlog = '/var/log/nginx/gunicorn-error.log'
        accesslog = '/var/log/nginx/gunicorn-access.log'
except:
    pass
