#!/bin/bash
source SAL_ENVS

if [ "$1" != "" ]; then
    BRANCH="$1"
else
    BRANCH="master"
fi

if [ "$BRANCH" != "master" ]; then
    TAG="$BRANCH"
else
    TAG="latest"
fi

URL="https://circleci.com/api/v1.1/project/github/salopensource/sal/tree/${BRANCH}"
echo $TAG
jq -n '{TAG: "$TAG"}' | curl -X POST -d @- \
  --user ${CIRCLE_API_USER_TOKEN}: \
  --url $URL \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json'
