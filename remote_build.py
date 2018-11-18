#!/usr/bin/python

import subprocess
import requests
import os
import argparse

parser = argparse.ArgumentParser(description='Process a build.')
parser.add_argument('build_tag', type=str, help='The tag to build.')

args = parser.parse_args()
print args.build_tag
