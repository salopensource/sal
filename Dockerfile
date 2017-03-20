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
    wget \
    supervisor \
    libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
ADD setup/requirements.txt /requirements.txt
RUN easy_install pip && \
    pip install -r /requirements.txt && \
    pip install psycopg2==2.6.2 && \
    pip install gunicorn==19.6.0 && \
    pip install setproctitle && \
    rm /requirements.txt && \
    update-rc.d -f postgresql remove && \
    mkdir -p /home/app && \
    mkdir -p /home/backup
ADD / $APP_DIR
ADD docker/settings.py $APP_DIR/sal/
ADD docker/supervisord.conf $APP_DIR/supervisord.conf
ADD docker/settings_import.py $APP_DIR/sal/
ADD docker/wsgi.py $APP_DIR/
ADD docker/gunicorn_config.py $APP_DIR/
ADD docker/run.sh /run.sh
ADD docker/nginx/nginx-env.conf /etc/nginx/main.d/
ADD docker/nginx/sal.conf /etc/nginx/sites-enabled/sal.conf
ADD docker/nginx/nginx.conf /etc/nginx/nginx.conf
ADD docker/crontab /etc/cron.d/search-maint
ADD docker/search_maint.sh /usr/local/bin/search_maint.sh

RUN chmod 755 /run.sh && \
    update-rc.d -f nginx remove && \
    rm -f /etc/nginx/sites-enabled/default && \
    ln -s $APP_DIR /home/app/sal && \
    chmod 644 /etc/cron.d/search-maint &&\
    chmod 755 /usr/local/bin/search_maint.sh

WORKDIR $APP_DIR
EXPOSE 8000

CMD ["/run.sh"]

VOLUME ["$APP_DIR/plugins"]
