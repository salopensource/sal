#!/usr/bin/python

import subprocess
import requests
import os
import argparse

parser = argparse.ArgumentParser(description='Process a build.')
parser.add_argument('build_tag', type=str, help='The tag to build.')

args = parser.parse_args()
print args.build_tag

project_username = os.getenv('CIRCLE_PROJECT_USERNAME')
api_user_token = os.getenv('CIRCLE_API_USER_TOKEN')
project_reponame = os.getenv('CIRCLE_PROJECT_REPONAME')

post_data = {}
post_data['build_parameters'] = {'TAG': args.build_tag}

url = "https://circleci.com/api/v1.1/project/github/{}/{}/tree/{}".format(
    project_username,
    project_reponame,
    args.build_tag
)

the_request = requests.post(url, json=post_data, auth=(api_user_token, ''))
print the_request.text
