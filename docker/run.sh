#!/bin/bash

function setBoolean() {
  local v
  if (( $# != 2 )); then
     echo "Err: setBoolean usage" 1>&2; exit 1 ;
  fi

  case "$2" in
    TRUE) v=true ;;
    FALSE) v=false ;;
    true) v=true ;;
    false) v=false ;;
    *) echo "Err: Unknown boolean value \"$2\"" 1>&2; exit 1 ;;
   esac

   eval $1=$v
}

cd $APP_DIR
ADMIN_PASS=${ADMIN_PASS:-}
DB_HOST=${DB_HOST:-}
DB_PORT_5432_TCP_ADDR=${DB_PORT_5432_TCP_ADDR:-}
DB_NAME=${DB_NAME:-}
DB_USER=${DB_USER:-}
DB_PASS=${DB_PASS:-}

# sleep 2

python manage.py migrate --noinput
python manage.py collectstatic --noinput

/bin/rm -f /var/run/gunicorn.pid

cron

if [ ! -z "$ADMIN_PASS" ] ; then
  python manage.py update_admin_user --username=admin --password=$ADMIN_PASS
else
  python manage.py update_admin_user --username=admin --password=password
fi

# tail -n 0 -f /var/log/gunicorn/gunicorn*.log & tail -n 0 -f $APP_DIR/sal.log &
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
