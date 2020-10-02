#!/bin/bash
source SAL_ENVS

if [ "$1" != "" ]; then
    BRANCH="$1"
else
    BRANCH="main"
fi

if [ "$BRANCH" != "main" ]; then
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
