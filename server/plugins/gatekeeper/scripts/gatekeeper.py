#!/usr/bin/python

import subprocess
import sys
sys.path.append('/usr/local/munki')
from munkilib import FoundationPlist
from munkilib import munkicommon
import os
import platform


def get_status(cmd, checkstring):
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = str(e.output)
    if checkstring in output:
        return 'Enabled'
    else:
        return 'Disabled'


def gatekeeper_status():
    cmd = ['/usr/sbin/spctl', '--status']
    return get_status(cmd, 'assessments enabled')


def main():

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
    result['plugin'] = 'Gatekeeper'
    result['historical'] = False
    data = {}
    data['Gatekeeper'] = gatekeeper
    result['data'] = data
    plist.append(result)
    FoundationPlist.writePlist(plist, plist_path)


if __name__ == '__main__':
    main()
