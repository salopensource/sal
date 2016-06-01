#!/usr/bin/python

import subprocess
from datetime import datetime, timedelta
import sys
sys.path.append('/usr/local/munki')
from munkilib import FoundationPlist
from munkilib import munkicommon
import os

def get_uptime():
    p = subprocess.Popen("/usr/bin/uptime".split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if 'days' in stdout:
        uptime_days = stdout.split()[2]
        uptime_hours, uptime_minutes = stdout.split()[4][:-1].split(":")
    else:
        uptime_days = 0
        uptime_hours, uptime_minutes = stdout.split()[2][:-1].split(":")
    uptime = timedelta(days=int(uptime_days), hours=int(uptime_hours), minutes=int(uptime_minutes))

    return (uptime.total_seconds(), uptime_minutes, uptime_hours, uptime_days)

def main():
    (uptime_seconds, uptime_minutes, uptime_hours, uptime_days) = get_uptime()
    
    plist_path = '/usr/local/sal/plugin_results.plist'

    if os.path.exists(plist_path):
        plist = FoundationPlist.readPlist(plist_path)
    else:
        plist = []
    result = {}
    result['plugin'] = 'Uptime'
    result['historical'] = False
    data = {}
    
    data['UptimeDays'] = uptime_days
    data['UptimeHours'] = uptime_hours
    data['UptimeMinutes'] = uptime_minutes
    data['TotalSeconds'] = uptime_seconds
    result['data'] = data
    plist.append(result)
    FoundationPlist.writePlist(plist, plist_path)

if __name__ == '__main__':
    main()

