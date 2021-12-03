#!/usr/local/sal/Python.framework/Versions/Current/bin/python3


import os
import re
import subprocess
import time

import sal


def main():
    uptime_seconds = get_uptime()
    data = {'UptimeDays': uptime_seconds / 60 / 60 / 24,
            'UptimeSeconds': uptime_seconds}
    sal.add_plugin_results('Uptime', data)


def get_uptime():
    cmd = ['/usr/sbin/sysctl', '-n', 'kern.boottime']
    p = subprocess.Popen(
        cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True)
    (output, unused_error) = p.communicate()
    sec = int(re.sub(r'.*sec = (\d+),.*', '\\1', output))
    up = int(time.time() - sec)
    return up if up > 0 else -1


if __name__ == '__main__':
    main()
