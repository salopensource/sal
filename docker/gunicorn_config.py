import multiprocessing
bind = '127.0.0.1:8001'
workers = multiprocessing.cpu_count() * 2 + 1
# errorlog = '/var/log/nginx/gunicorn-error.log'
# accesslog = '/var/log/nginx/gunicorn-access.log'