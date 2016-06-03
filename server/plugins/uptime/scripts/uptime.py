#!/usr/bin/python

import subprocess
import time
import sys
sys.path.append('/usr/local/munki')
from munkilib import FoundationPlist
from munkilib import munkicommon
import os
import re

def get_uptime():
    cmd = ['/usr/sbin/sysctl', '-n', 'kern.boottime']
    p = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, unused_error) = p.communicate()
    sec = int(re.sub('.*sec = (\d+),.*', '\\1', output))
    up = int(time.time() - sec)
    return up if up > 0 else -1

def main():
    uptime_seconds = get_uptime()
    
    plist_path = '/usr/local/sal/plugin_results.plist'

    if os.path.exists(plist_path):
        plist = FoundationPlist.readPlist(plist_path)
    else:
        plist = []
    result = {}
    result['plugin'] = 'Uptime'
    result['historical'] = False
    data = {}
    
    data['UptimeDays'] = uptime_seconds / 60 / 60 / 24
    result['data'] = data
    plist.append(result)
    FoundationPlist.writePlist(plist, plist_path)

if __name__ == '__main__':
    main()

