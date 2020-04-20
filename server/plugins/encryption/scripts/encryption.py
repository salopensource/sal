#!/usr/local/sal/Python.framework/Versions/3.8/bin/python3


import os
import subprocess

import sal


def main():
    status = filevault_status()
    sal.add_plugin_results('Encryption', {'FileVault': status})


def filevault_status():
    if not os.path.exists('/usr/bin/fdesetup'):
        status = 'Not Supported'
    else:
        cmd = ['/usr/bin/fdesetup', 'status']
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as error:
            output = str(error.output)

        status = 'Enabled' if 'FileVault is On' in output else 'Disabled'

    return status


if __name__ == '__main__':
    main()
