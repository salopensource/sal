#!/bin/bash

CWD=`pwd`
docker ps -aq | xargs docker rm -f

docker run -d \
    -e ADMIN_PASS=pass \
    -e DOCKER_SAL_BRUTE_PROTECT="false" \
    -e DOCKER_SAL_DEBUG="true" \
    --name=sal \
    --restart="always" \
    -v "$CWD/sal.db":/home/docker/sal/db/sal.db \
    -p 8000:8000 \
    macadmins/sal
