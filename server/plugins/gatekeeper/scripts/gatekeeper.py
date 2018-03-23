#!/usr/bin/python


import os
import subprocess
import sys

sys.path.append('/usr/local/munki')
from munkilib import FoundationPlist


def main():
    add_plugin_results('Gatekeeper', {'Gatekeeper': gatekeeper_status()})


def gatekeeper_status():
    if not os.path.exists('/usr/sbin/spctl'):
        status = 'Not Supported'
    else:

        cmd = ['/usr/sbin/spctl', '--status']
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            output = str(error.output)
        status = 'Enabled' if 'assessments enabled' in output else 'Disabled'

    return status


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


if __name__ == '__main__':
    main()
