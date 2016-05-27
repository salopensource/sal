#!/usr/bin/python

import sys
sys.path.append('/usr/local/munki')
from munkilib import FoundationPlist
import subprocess
import os
from pprint import pprint
import json
import CoreFoundation

def main():
    # Skip a manual check
    if len(sys.argv) > 1:
        if sys.argv[1] == 'manualcheck':
            munkicommon.display_debug2("Manual check: skipping SecurityReport Plugin.")
            exit(0)

    plist_path = '/usr/local/sal/plugin_results.plist'
    if os.path.exists(plist_path):
        plist = FoundationPlist.readPlist(plist_path)
    else:
        plist = []

    # Make sure osqueryi exists
    if os.path.exists('/usr/local/bin/osqueryi'):
        osquery_result = process_osquery()

    # get screensaver settings
    screensaver = screensaver_status()
    filevault = filevault_status()
    firewall = firewall_status()
    result = {}
    result['plugin'] = 'SecurityReport'
    result['historical'] = False
    data = {}
    data = merge_dicts(osquery_result, screensaver, filevault, firewall)

    result['data'] = data
    plist.append(result)
    FoundationPlist.writePlist(plist, plist_path)

def merge_dicts(*dict_args):
    '''
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    '''
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result

def process_osquery():
    osquery_result = {}
    osx_attacks = '/private/var/osquery/packs/osx-attacks.conf'
    if os.path.exists(osx_attacks):
        with open(osx_attacks) as osx_attacks_file:
            json_data = json.load(osx_attacks_file)
            for name, value in json_data['queries'].iteritems():
                output_json = subprocess.check_output(['/usr/local/bin/osqueryi', '--json', value['query']])
                output = json.loads(output_json)
                # Don't log empty json, this is easier to search on
                target_name = 'osx-attacks: %s' % name
                if len(output) == 0:
                    osquery_result[target_name] = output
                else:
                    osquery_result[target_name] = output_json
    return osquery_result

def screensaver_status():
    output = {}
    output['screensaver_askForPassword'] = CoreFoundation.CFPreferencesCopyAppValue("askForPassword", "com.apple.screensaver")
    output['screensaver_askForPasswordDelay'] = CoreFoundation.CFPreferencesCopyAppValue("askForPasswordDelay", "com.apple.screensaver")
    return output

def filevault_status():
    if os.path.exists('/usr/bin/fdesetup'):
        output = {}
        output['fdesetup_status'] = subprocess.check_output(['/usr/bin/fdesetup', 'status']).strip()
        return output
    else:
        return {}

def firewall_status():
    output = {}
    output['firewall_enabled'] = CoreFoundation.CFPreferencesCopyAppValue("globalstate", "com.apple.alf")
    return output

if __name__ == '__main__':
    main()
