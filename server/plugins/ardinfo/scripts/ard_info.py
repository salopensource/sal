#!/usr/bin/python


import os
import sys

sys.path.append("/usr/local/munki/munkilib")
import FoundationPlist


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

    add_plugin_results('ARD_Info', data)


def add_plugin_results(plugin, data, historical=False):
    """Add data to the shared plugin results plist.

    This function creates the shared results plist file if it does not
    already exist; otherwise, it adds the entry by appending.

    Args:
        plugin (str): Name of the plugin returning data.
        data (dict): Dictionary of results.
        historical (bool): Whether to keep only one record (False) or
            all results (True). Optional, defaults to False.
    """
    plist_path = '/usr/local/sal/plugin_results.plist'
    if os.path.exists(plist_path):
        plugin_results = FoundationPlist.readPlist(plist_path)
    else:
        plugin_results = []

    plugin_results.append({'plugin': plugin, 'historical': historical, 'data': data})
    FoundationPlist.writePlist(plugin_results, plist_path)


if __name__ == "__main__":
    main()
