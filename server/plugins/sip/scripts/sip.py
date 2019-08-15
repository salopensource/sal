#!/usr/bin/python


import os
import subprocess
import sys

sys.path.append("/usr/local/sal")
import utils


def main():
    utils.add_plugin_results('Sip', {'SIP': sip_status()})


def sip_status():
    if not os.path.exists('/usr/bin/csrutil'):
        status = 'Not Supported'
    else:
        cmd = ['/usr/bin/csrutil', 'status']
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            output = str(error.output)

        enabled = 'System Integrity Protection status: enabled.'
        status = 'Enabled' if enabled in output else 'Disabled'

    return status


if __name__ == '__main__':
    main()
