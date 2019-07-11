#!/usr/bin/python


import os
import subprocess
import sys

sys.path.append("/usr/local/sal")
import utils


def main():
    filevault = fv_status()
    sip = sip_status()
    gatekeeper = gatekeeper_status()
    data = {'Filevault': filevault, 'SIP': sip, 'Gatekeeper': gatekeeper}
    utils.add_plugin_results('MachineDetailSecurity', data)


def fv_status():
    cmd = ['/usr/bin/fdesetup', 'status']
    return get_status(cmd, 'FileVault is On.', '/usr/bin/fdesetup')


def sip_status():
    cmd = ['/usr/bin/csrutil', 'status']
    return get_status(cmd, 'System Integrity Protection status: enabled.', '/usr/bin/csrutil')


def gatekeeper_status():
    cmd = ['/usr/sbin/spctl', '--status']
    return get_status(cmd, 'assessments enabled', '/usr/sbin/spctl')


def get_status(cmd, checkstring, test=''):
    if test and not os.path.exists(test):
        status = 'Not Supported'
    else:
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            output = str(error.output)
        status = 'Enabled' if checkstring in output else 'Disabled'

    return status


if __name__ == '__main__':
    main()
