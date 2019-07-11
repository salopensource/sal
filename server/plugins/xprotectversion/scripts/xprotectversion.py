#!/usr/bin/python


import os
import sys

sys.path.append('/usr/local/munki')
from munkilib import FoundationPlist
sys.path.append("/usr/local/sal")
import utils


def main():
    plist_path = (
        '/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/XProtect.meta.plist')
    if os.path.exists(plist_path):
        plist = FoundationPlist.readPlist(plist_path)
        version = str(plist['Version'])
    else:
        version = 'Not supported'

    utils.add_plugin_results('XprotectVersion', {'Version': version})


if __name__ == '__main__':
    main()
