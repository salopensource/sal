#!/bin/bash

CWD=`pwd`
docker rm -f sal

docker run -d \
    -e ADMIN_PASS=pass \
    -e DB_NAME=sal \
    -e DB_USER=admin \
    -e DB_PASS=password \
    -e DOCKER_SAL_DEBUG="true" \
    -v "$CWD/sal/settings.py:/home/app/sal/sal/settings.py" \
    --link postgres-sal:db \
    --name=sal \
    -p 8000:8000 \
    macadmins/sal
