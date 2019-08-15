#!/usr/bin/python


import os
import re
import subprocess
import sys
import time

sys.path.append("/usr/local/sal")
import utils


def main():
    uptime_seconds = get_uptime()
    data = {'UptimeDays': uptime_seconds / 60 / 60 / 24,
            'UptimeSeconds': uptime_seconds}
    utils.add_plugin_results('Uptime', data)


def get_uptime():
    cmd = ['/usr/sbin/sysctl', '-n', 'kern.boottime']
    p = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, unused_error) = p.communicate()
    sec = int(re.sub(r'.*sec = (\d+),.*', '\\1', output))
    up = int(time.time() - sec)
    return up if up > 0 else -1


if __name__ == '__main__':
    main()
