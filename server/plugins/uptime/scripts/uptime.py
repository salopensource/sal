#!/usr/bin/python


import os
import re
import subprocess
import sys
import time

sys.path.append('/usr/local/munki')
from munkilib import FoundationPlist


def main():
    uptime_seconds = get_uptime()
    data = {'UptimeDays': uptime_seconds / 60 / 60 / 24,
            'UptimeSeconds': uptime_seconds}
    add_plugin_results('Uptime', data)


def get_uptime():
    cmd = ['/usr/sbin/sysctl', '-n', 'kern.boottime']
    p = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, unused_error) = p.communicate()
    sec = int(re.sub(r'.*sec = (\d+),.*', '\\1', output))
    up = int(time.time() - sec)
    return up if up > 0 else -1


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
