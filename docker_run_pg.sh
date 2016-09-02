#!/bin/bash

CWD=`pwd`
docker ps -aq | xargs docker rm -f

docker run -d --name="postgres-sal" \
    -e DB_NAME=sal \
    -e DB_USER=admin \
    -e DB_PASS=password \
    --restart="always" \
    -v "$CWD"/test-pg-db:/var/lib/postgresql/data \
    grahamgilbert/postgres:9.4.5

sleep 10

docker build -t "macadmins/sal" .

docker run -d \
    -e ADMIN_PASS=pass \
    -e DB_NAME=sal \
    -e DB_USER=admin \
    -e DB_PASS=password \
    -e DOCKER_SAL_BRUTE_PROTECT="false" \
    -e DOCKER_SAL_DEBUG="true" \
    --link postgres-sal:db \
    --name=sal \
    --restart="always" \
    -p 8000:8000 \
    macadmins/sal
