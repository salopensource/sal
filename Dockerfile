# Sal Dockerfile
# Version 0.4
FROM ubuntu:14.04.5

MAINTAINER Graham Gilbert <graham@grahamgilbert.com>

ENV HOME /root
ENV DEBIAN_FRONTEND noninteractive
ENV APPNAME Sal
ENV APP_DIR /home/docker/sal
ENV DOCKER_SAL_TZ Europe/London
ENV DOCKER_SAL_ADMINS Docker User, docker@localhost
ENV DOCKER_SAL_LANG en_GB
ENV DOCKER_SAL_DISPLAY_NAME Sal
ENV DOCKER_SAL_DEBUG false
ENV WAIT_FOR_POSTGRES false
# ENV DOCKERIZE_VERSION v0.3.0

RUN apt-get update && \
    apt-get install -y libc-bin && \
    apt-get install -y software-properties-common && \
    apt-get -y update && \
    add-apt-repository -y ppa:nginx/stable && \
    apt-get -y install \
    git \
    nginx \
    python-setuptools \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    python-dev \
    curl \
    supervisor \
    libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
# && \
# wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
#    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
#    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz &&\
COPY setup/requirements.txt /requirements.txt
RUN easy_install pip && \
    pip install -r /requirements.txt && \
    pip install psycopg2==2.6.2 && \
    pip install gunicorn==19.6.0 && \
    pip install setproctitle && \
    rm /requirements.txt && \
    update-rc.d -f postgresql remove && \
    update-rc.d -f nginx remove && \
    mkdir -p /home/app && \
    mkdir -p /home/backup
COPY / $APP_DIR
COPY docker/settings.py $APP_DIR/sal/
COPY docker/supervisord.conf $APP_DIR/supervisord.conf
COPY docker/settings_import.py $APP_DIR/sal/
COPY docker/wsgi.py $APP_DIR/
COPY docker/gunicorn_config.py $APP_DIR/
COPY docker/run.sh /run.sh
COPY docker/nginx/nginx-env.conf /etc/nginx/main.d/
COPY docker/nginx/sal.conf /etc/nginx/sites-enabled/sal.conf
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY docker/crontab /etc/cron.d/search-maint
COPY docker/search_maint.sh /usr/local/bin/search_maint.sh

RUN chmod 755 /run.sh && \
    rm -f /etc/nginx/sites-enabled/default && \
    ln -s $APP_DIR /home/app/sal && \
    chmod 644 /etc/cron.d/search-maint &&\
    chmod 755 /usr/local/bin/search_maint.sh &&\
    mkdir -p /var/log/gunicorn &&\
    touch /var/log/gunicorn/gunicorn-error.log &&\
    touch /var/log/gunicorn/gunicorn-access.log &&\
    chown -R www-data:www-data $APP_DIR &&\
    chmod go+x $APP_DIR &&\
    touch $APP_DIR/sal.log &&\
    chmod 777 $APP_DIR/sal.log

WORKDIR $APP_DIR
EXPOSE 8000

CMD ["/run.sh"]

VOLUME ["$APP_DIR/plugins"]
