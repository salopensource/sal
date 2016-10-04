#!/bin/bash

CWD=`pwd`
docker rm -f sal

docker run -d \
    -e ADMIN_PASS=pass \
    -e DB_NAME=sal \
    -e DB_USER=admin \
    -e DB_PASS=password \
    -e DOCKER_SAL_BRUTE_PROTECT="false" \
    -e DOCKER_SAL_DEBUG="false" \
    --link postgres-sal:db \
    --name=sal \
    --restart="always" \
    -p 8000:8000 \
    macadmins/sal
