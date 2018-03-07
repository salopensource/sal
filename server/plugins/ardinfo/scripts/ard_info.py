#!/usr/bin/python


import os
import sys

sys.path.append("/usr/local/munki/munkilib")
import FoundationPlist


RESULTS_PATH = "/usr/local/sal/plugin_results.plist"


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
        for i in xrange(1, 5)}

    formatted_results = {
        "plugin": "ARD_Info",
        "historical": False,
        "data": data}

    if os.path.exists(RESULTS_PATH):
        plugin_results = FoundationPlist.readPlist(RESULTS_PATH)
    else:
        plugin_results = []

    plugin_results.append(formatted_results)

    FoundationPlist.writePlist(plugin_results, RESULTS_PATH)


if __name__ == "__main__":
    main()
