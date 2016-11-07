#!/bin/bash

cd /usr/local/sal_install/sal
export PYTHONPATH=/usr/local/sal_install/sal/sal:$PYTHONPATH
export DJANGO_SETTINGS_MODULE='sal.settings'

/usr/local/sal_install/sal_env/bin/python manage.py search_maintenance
