#!/bin/bash
source SAL_ENVS

if [ "$1" != "" ]; then
    BRANCH="$1"
else
    BRANCH="master"
fi

URL="https://circleci.com/api/v1.1/project/github/salopensource/sal/tree/${BRANCH}"

jq -n '{TAG: "latest"}' | curl -X POST -d @- \
  --user ${CIRCLE_API_USER_TOKEN}: \
  --url $URL \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json'
