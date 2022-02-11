#!/usr/local/sal/Python.framework/Versions/Current/bin/python3


import pathlib
import plistlib

import sal


def main():
    plist_path = pathlib.Path(
        '/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/XProtect.meta.plist')
    if plist_path.exists():
        plist = plistlib.loads(plist_path.read_bytes())
        version = str(plist['Version'])
    else:
        version = 'Not supported'

    sal.add_plugin_results('XprotectVersion', {'Version': version})


if __name__ == '__main__':
    main()
