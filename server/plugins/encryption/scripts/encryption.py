#!/usr/bin/python


import os
import subprocess
import sys

sys.path.append("/usr/local/sal")
import utils


def main():
    status = filevault_status()
    utils.add_plugin_results('Encryption', {'FileVault': status})


def filevault_status():
    if not os.path.exists('/usr/bin/fdesetup'):
        status = 'Not Supported'
    else:
        cmd = ['/usr/bin/fdesetup', 'status']
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            output = str(error.output)

        status = 'Enabled' if 'FileVault is On' in output else 'Disabled'

    return status


if __name__ == '__main__':
    main()
