#!/usr/local/sal/Python.framework/Versions/Current/bin/python3


import pathlib
import plistlib
import os

import sal



def xprotect_version():
    try:
        darwin_ver = int(os.uname().release.split('.')[0])
    except:
        return 'Not supported'
    if darwin_ver >= 20:  # Big Sur 11.x
        xprotect = '/Library/Apple/System/Library/CoreServices/XProtect.bundle/Contents/Info.plist'
        key = 'CFBundleShortVersionString'
    else:
        xprotect = '/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/XProtect.meta.plist'
        key = 'Version'
    plist_path = pathlib.Path(xprotect)
    if plist_path.exists():
        plist = plistlib.loads(plist_path.read_bytes())
        return str(int(plist[key]))
    else:
        return 'Not supported'


def main():
    version = xprotect_version()
    sal.add_plugin_results('XprotectVersion', {'Version': version})

if __name__ == '__main__':
    main()
