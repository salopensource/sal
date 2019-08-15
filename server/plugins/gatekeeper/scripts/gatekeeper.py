#!/usr/bin/python


import os
import subprocess
import sys

sys.path.append("/usr/local/sal")
import utils


def main():
    utils.add_plugin_results('Gatekeeper', {'Gatekeeper': gatekeeper_status()})


def gatekeeper_status():
    if not os.path.exists('/usr/sbin/spctl'):
        status = 'Not Supported'
    else:

        cmd = ['/usr/sbin/spctl', '--status']
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            output = str(error.output)
        status = 'Enabled' if 'assessments enabled' in output else 'Disabled'

    return status


if __name__ == '__main__':
    main()
