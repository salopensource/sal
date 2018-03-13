#!/usr/bin/python


import os
import subprocess
import sys

sys.path.append('/usr/local/munki')
from munkilib import FoundationPlist


def main():
    filevault = fv_status()
    sip = sip_status()
    gatekeeper = gatekeeper_status()
    data = {'Filevault': filevault, 'SIP': sip, 'Gatekeeper': gatekeeper}
    add_plugin_results('MachineDetailSecurity', data)


def fv_status():
    cmd = ['/usr/bin/fdesetup', 'status']
    return get_status(cmd, 'FileVault is On.', '/usr/bin/fdesetup')


def sip_status():
    cmd = ['/usr/bin/csrutil', 'status']
    return get_status(cmd, 'System Integrity Protection status: enabled.', '/usr/bin/csrutil')


def gatekeeper_status():
    cmd = ['/usr/sbin/spctl', '--status']
    return get_status(cmd, 'assessments enabled', '/usr/sbin/spctl')


def get_status(cmd, checkstring, test=''):
    if test and not os.path.exists(test):
        status = 'Not Supported'
    else:
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            output = str(error.output)
        status = 'Enabled' if checkstring in output else 'Disabled'

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
