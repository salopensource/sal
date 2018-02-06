#!/usr/bin/python

import subprocess
import sys
sys.path.append('/usr/local/munki')
from munkilib import FoundationPlist
from munkilib import munkicommon
import os
import platform
from distutils.version import LooseVersion


def mac_version():
    v = platform.mac_ver()[0][:-2]
    return v


def get_status(cmd, checkstring):
    status = 'Disabled'
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = str(e.output)

    for line in output.split('\n'):
        if checkstring in line:
            status = 'Enabled'
            break
    return status


def fv_status():
    cmd = ['/usr/bin/fdesetup', 'status']
    return get_status(cmd, 'FileVault is On.')


def sip_status():
    cmd = ['/usr/bin/csrutil', 'status']
    return get_status(cmd, 'System Integrity Protection status: enabled.')


def gatekeeper_status():
    cmd = ['/usr/sbin/spctl', '--status']
    return get_status(cmd, 'assessments enabled')


def main():

    if os.path.exists('/usr/bin/fdesetup'):
        filevault = fv_status()
    else:
        filevault = 'Not Supported'

    if os.path.exists('/usr/bin/csrutil'):
        sip = sip_status()
    else:
        sip = 'Not Supported'

    # Yes, I know it came in 10.7.5, but eh. I don't care, I'm lazy
    if os.path.exists('/usr/sbin/spctl'):
        gatekeeper = gatekeeper_status()
    else:
        gatekeeper = 'Not Supported'

    plist_path = '/usr/local/sal/plugin_results.plist'

    if os.path.exists(plist_path):
        plist = FoundationPlist.readPlist(plist_path)
    else:
        plist = []
    result = {}
    result['plugin'] = 'MachineDetailSecurity'
    result['historical'] = False
    data = {}

    data['Filevault'] = filevault
    data['SIP'] = sip
    data['Gatekeeper'] = gatekeeper
    result['data'] = data
    plist.append(result)
    print plist
    FoundationPlist.writePlist(plist, plist_path)


if __name__ == '__main__':
    main()
