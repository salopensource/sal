#!/usr/bin/python

import subprocess
import sys
sys.path.append('/usr/local/munki')
from munkilib import FoundationPlist
from munkilib import munkicommon
import os
import platform
from distutils.version import LooseVersion


def main():
    plist_path = '/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/XProtect.meta.plist'
    if os.path.exists(plist_path):
        plist = FoundationPlist.readPlist(plist_path)
        version = str(plist['Version'])
    else:
        version = 'Not supported'

    plist_path = '/usr/local/sal/plugin_results.plist'

    if os.path.exists(plist_path):
        plist = FoundationPlist.readPlist(plist_path)
    else:
        plist = []
    result = {}
    result['plugin'] = 'XprotectVersion'
    result['historical'] = False
    data = {}
    data['Version'] = version
    result['data'] = data
    plist.append(result)
    FoundationPlist.writePlist(plist, plist_path)


if __name__ == '__main__':
    main()
