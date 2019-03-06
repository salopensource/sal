#!/usr/bin/python


import argparse
import os
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
    options = args.options if args.options else []
    for option in options:
        cmd += ' -{}'.format(option)
    if args.edit and 'l' not in options:
        cmd += ' -l'
    cmd += " '{}'".format(r'\|'.join(args.search_terms))
    cmd += ' *'

    try:
        results = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
        # Most common error is that there are no results!
        results = ''
    print(results.strip())

    if args.edit and results:
        subprocess.check_call([os.getenv('EDITOR')] + [l.strip() for l in results.splitlines()])


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('search_terms', nargs='*')
    parser.add_argument('--options', nargs='*')
    msg = 'Open files with matches in {}.'.format(os.getenv('EDITOR') or '<No EDITOR set>')
    parser.add_argument('--edit', action='store_true', help=msg)
    return parser.parse_args()


if __name__ == "__main__":
    main()
