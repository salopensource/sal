#!/bin/bash

cd $APP_DIR
ADMIN_PASS=${ADMIN_PASS:-}
# service monit stop
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py friendly_model_name

if [ ! -z "$ADMIN_PASS" ] ; then
  python manage.py update_admin_user --username=admin --password=$ADMIN_PASS
else
  python manage.py update_admin_user --username=admin --password=password
fi


chown -R www-data:www-data $APP_DIR
chmod go+x $APP_DIR
mkdir -p /var/log/gunicorn
touch /var/log/gunicorn/gunicorn-error.log
touch /var/log/gunicorn/gunicorn-access.log
touch $APP_DIR/sal.log
chmod 777 $APP_DIR/sal.log
tail -n 0 -f /var/log/gunicorn/gunicorn*.log & tail -n 0 -f $APP_DIR/sal.log &
export PYTHONPATH=$PYTHONPATH:$APP_DIR
export DJANGO_SETTINGS_MODULE='sal.settings'


if [ "$DOCKER_SAL_DEBUG" = "true" ] || [ "$DOCKER_SAL_DEBUG" = "True" ] || [ "$DOCKER_SAL_DEBUG" = "TRUE" ] ; then
    service nginx stop
    echo "RUNNING IN DEBUG MODE"
    python manage.py runserver 0.0.0.0:8000
else
  supervisord --nodaemon -c $APP_DIR/supervisord.conf
fi
