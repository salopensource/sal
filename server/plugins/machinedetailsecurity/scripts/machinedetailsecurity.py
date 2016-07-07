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
    output = subprocess.check_output(cmd)
    if checkstring in output:
        return 'Enabled'
    else:
        return 'Disabled'

def fv_status():
    cmd = ['/usr/bin/fdesetup', 'status']
    return get_status(cmd, 'FileVault is On.')

def sip_status():
    cmd = ['/usr/bin/csrutil', 'status']
    return get_status(cmd, 'System Integrity Protection status: enabled.')

def main():
    filevault = fv_status()
    
    mac_ver = mac_version()

    if LooseVersion("10.11") <= LooseVersion(mac_ver):
        sip = sip_status()
    else:
        sip = 'Not Supported'

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
    result['data'] = data
    plist.append(result)
    FoundationPlist.writePlist(plist, plist_path)

if __name__ == '__main__':
    main()

