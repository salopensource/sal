#!/bin/bash
cd /home/app/sal
/usr/local/bin/gunicorn -D -c gunicorn_config.py sal.wsgi
