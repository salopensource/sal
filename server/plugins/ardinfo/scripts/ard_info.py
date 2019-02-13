#!/usr/bin/python


import os
import sys

sys.path.append("/usr/local/munki/munkilib")
import FoundationPlist
sys.path.append("/usr/local/sal")
import utils


def main():
    ard_path = "/Library/Preferences/com.apple.RemoteDesktop.plist"
    if os.path.exists(ard_path):
        ard_prefs = FoundationPlist.readPlist(ard_path)
    else:
        ard_prefs = {}

    sal_result_key = "ARD_Info_{}"
    prefs_key_prefix = "Text{}"

    data = {
        sal_result_key.format(i): ard_prefs.get(prefs_key_prefix.format(i), "")
        for i in range(1, 5)}

    utils.add_plugin_results('ARD_Info', data)


if __name__ == "__main__":
    main()
