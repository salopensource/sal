#!/usr/bin/python

import subprocess
import sys
sys.path.append('/usr/local/munki')
from munkilib import FoundationPlist
from munkilib import munkicommon
import os

def fv_status():
    cmd = ['/usr/bin/fdesetup', 'status']
    fv_output = subprocess.check_output(cmd)
    if 'FileVault is On.' in fv_output:
        return 'Enabled'
    else:
        return 'Disabled'

def main():
    filevault = fv_status()
    
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
    result['data'] = data
    plist.append(result)
    FoundationPlist.writePlist(plist, plist_path)

if __name__ == '__main__':
    main()

