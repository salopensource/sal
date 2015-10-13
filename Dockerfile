# Sal Dockerfile
# Version 0.3
FROM ubuntu:14.04.1

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

ADD / $APP_DIR
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    apt-get -y update && \
    add-apt-repository -y ppa:nginx/stable && \
    apt-get -y install \
    git \
    python-setuptools \
    nginx \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    python-dev \
    supervisor \
    nano \
    libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN easy_install pip && \
    pip install -r $APP_DIR/setup/requirements.txt && \
    pip install psycopg2==2.5.3 && \
    pip install gunicorn && \
    pip install setproctitle
ADD docker/nginx/nginx-env.conf /etc/nginx/main.d/
ADD docker/nginx/sal.conf /etc/nginx/sites-enabled/sal.conf
ADD docker/nginx/nginx.conf /etc/nginx/nginx.conf
ADD docker/settings.py $APP_DIR/sal/
ADD docker/settings_import.py $APP_DIR/sal/
ADD docker/brute_settings.py $APP_DIR/sal/
ADD docker/wsgi.py $APP_DIR/
ADD docker/gunicorn_config.py $APP_DIR/
ADD docker/django/management/ $APP_DIR/sal/management/
ADD docker/run.sh /run.sh
ADD docker/supervisord.conf $APP_DIR/supervisord.conf

RUN update-rc.d -f postgresql remove && \
    update-rc.d -f nginx remove && \
    rm -f /etc/nginx/sites-enabled/default && \
    mkdir -p /home/app && \
    mkdir -p /home/backup && \
    ln -s $APP_DIR /home/app/sal

EXPOSE 8000

CMD ["/run.sh"]

VOLUME ["$APP_DIR/plugins"]
