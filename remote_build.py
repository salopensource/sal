#!/usr/bin/python

import subprocess
import requests
import os
import argparse

parser = argparse.ArgumentParser(description="Process a build.")
parser.add_argument("build_tag", type=str, help="The tag to build.")

args = parser.parse_args()

api_user_token = os.getenv("CIRCLE_API_USER_TOKEN")
project_reponame = "sal-saml"
project_username = "salopensource"

post_data = {}
post_data["build_parameters"] = {"TAG": args.build_tag}

url = "https://circleci.com/api/v1.1/project/github/{}/{}/tree/main".format(
    project_username, project_reponame
)

the_request = requests.post(url, json=post_data, auth=(api_user_token, ""))
if the_request.status_code == requests.codes.ok:
    print(the_request.json)
else:
    print(the_request.text)
