#!/bin/bash

cd $APP_DIR
ADMIN_PASS=${ADMIN_PASS:-}
DB_HOST=${DB_HOST:-}
DB_PORT_5432_TCP_ADDR=${DB_PORT_5432_TCP_ADDR:-}
if [ ! -z "$DB_HOST" ] ; then
  echo "Waiting for database to come up"
  /usr/local/bin/dockerize -wait tcp://$DB_HOST:5432
  echo "Database is up, continuing"
elif [ ! -z "$DB_PORT_5432_TCP_ADDR" ] ; then
  echo "Waiting for database to come up"
  /usr/local/bin/dockerize -wait tcp://$DB_PORT_5432_TCP_ADDR:5432
  echo "Database is up, continuing"
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput
# python manage.py installwatson
python manage.py friendly_model_name
# python manage.py search_maintenance

cron

if [ ! -z "$ADMIN_PASS" ] ; then
  python manage.py update_admin_user --username=admin --password=$ADMIN_PASS
else
  python manage.py update_admin_user --username=admin --password=password
fi

tail -n 0 -f /var/log/gunicorn/gunicorn*.log & tail -n 0 -f $APP_DIR/sal.log &
export PYTHONPATH=$PYTHONPATH:$APP_DIR
export DJANGO_SETTINGS_MODULE='sal.settings'

printenv | sed 's/^\(.*\)$/export \1/g' > /env_vars.sh

if [ "$DOCKER_SAL_DEBUG" = "true" ] || [ "$DOCKER_SAL_DEBUG" = "True" ] || [ "$DOCKER_SAL_DEBUG" = "TRUE" ] ; then
    service nginx stop
    echo "RUNNING IN DEBUG MODE"
    python manage.py runserver 0.0.0.0:8000
else
  supervisord --nodaemon -c $APP_DIR/supervisord.conf
fi
