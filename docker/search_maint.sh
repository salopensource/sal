#!/bin/bash

cd /home/docker/sal
export PYTHONPATH=/home/docker/sal:$PYTHONPATH
export DJANGO_SETTINGS_MODULE='sal.settings'
source /env_vars.sh

python manage.py search_maintenance
