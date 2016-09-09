#!/bin/bash
cd $APP_DIR
/usr/local/bin/gunicorn -D -c gunicorn_config.py sal.wsgi
