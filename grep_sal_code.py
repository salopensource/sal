#!/usr/bin/python


import argparse
import subprocess
import sys


EXCLUSIONS = ['*.pyc', '*.log', 'venv*', 'static/*', 'site_static/*', 'datatableview/*', '*.db']


def main():
    args = parse_args()
    # Normally we like to build subprocess commands in lists, but it's
    # a lot easier to do all of the globbing we want with shell=True,
    # so we'll build up a string.
    cmd = 'grep -R --colour=always '
    cmd += " ".join("--exclude='{}'".format(i) for i in EXCLUSIONS)
    for option in args.options or []:
        cmd += ' -{}'.format(option)
    cmd += " '{}'".format(r'\|'.join(args.search_terms))
    cmd += ' *'

    try:
        results = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
        # Most common error is that there are no results!
        results = ''
    print results.strip()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('search_terms', nargs='*')
    parser.add_argument('--options', nargs='*')
    return parser.parse_args()


if __name__ == "__main__":
    main()