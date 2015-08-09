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
ENV DOCKER_SAL_PLUGIN_ORDER Activity,Status,OperatingSystem,Uptime,Memory
ENV DOCKER_SAL_DEBUG false

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
    git clone https://github.com/salopensource/sal.git $APP_DIR && \
    pip install -r $APP_DIR/setup/requirements.txt && \
    pip install psycopg2==2.5.3 && \
    pip install gunicorn && \
    pip install setproctitle

ADD nginx/nginx-env.conf /etc/nginx/main.d/
ADD nginx/sal.conf /etc/nginx/sites-enabled/sal.conf
ADD nginx/nginx.conf /etc/nginx/nginx.conf
ADD settings.py $APP_DIR/sal/
ADD settings_import.py $APP_DIR/sal/
ADD wsgi.py $APP_DIR/
ADD gunicorn_config.py $APP_DIR/
ADD django/management/ $APP_DIR/sal/management/
ADD run.sh /run.sh
ADD supervisord.conf $APP_DIR/supervisord.conf

RUN update-rc.d -f postgresql remove && \
    update-rc.d -f nginx remove && \
    rm -f /etc/nginx/sites-enabled/default && \
    mkdir -p /home/app && \
    mkdir -p /home/backup && \
    ln -s $APP_DIR /home/app/sal

EXPOSE 8000

CMD ["/run.sh"]

#VOLUME ["$APP_DIR/plugins", "$APP_DIR/sal/settings.py"]
