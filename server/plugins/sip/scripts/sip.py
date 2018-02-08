#!/usr/bin/python

import subprocess
import sys
sys.path.append('/usr/local/munki')
from munkilib import FoundationPlist
import os


def get_status(cmd, checkstring):
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = str(e.output)
    if checkstring in output:
        return 'Enabled'
    else:
        return 'Disabled'


def sip_status():
    cmd = ['/usr/bin/csrutil', 'status']
    return get_status(cmd, 'System Integrity Protection status: enabled.')


def main():

    if os.path.exists('/usr/bin/csrutil'):
        sip = sip_status()
    else:
        sip = 'Not Supported'

    plist_path = '/usr/local/sal/plugin_results.plist'

    if os.path.exists(plist_path):
        plist = FoundationPlist.readPlist(plist_path)
    else:
        plist = []
    result = {}
    result['plugin'] = 'Sip'
    result['historical'] = False
    data = {}
    data['SIP'] = sip
    result['data'] = data
    plist.append(result)
    FoundationPlist.writePlist(plist, plist_path)


if __name__ == '__main__':
    main()
