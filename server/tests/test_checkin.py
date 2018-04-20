"""Tests for the checkin process."""


import re

from django.test import TestCase

import server.non_ui_views


class InstallLogTest(TestCase):
    """Test the install log checkin code."""

    def test_install_regex(self):
        """"""
        for line in INSTALL_LOG.splitlines():
            match = re.search(server.non_ui_views.INSTALL_PATTERN, line)
            if not match.group('removal'):
                self.assertTrue(match is not None)
                for key in ('date', 'name', 'version', 'status'):
                    self.assertTrue(match.group(key) is not None)
                self.assertTrue(
                    match.group('apple_install') is not None or
                    match.group('third_party_install') is not None)

    def test_third_party_install_regex(self):
        for line in INSTALL_LOG.splitlines():
            match = re.search(server.non_ui_views.INSTALL_PATTERN, line)
            if not match.group('removal') and 'Apple Software Update install' not in line:
                self.assertTrue(match is not None)
                self.assertTrue(match.group('third_party_install') is not None)

    def test_apple_install_regex(self):
        for line in INSTALL_LOG.splitlines():
            match = re.search(server.non_ui_views.INSTALL_PATTERN, line)
            if not match.group('removal') and 'Apple Software Update install' in line:
                self.assertTrue(match is not None)
                self.assertTrue(match.group('third_party_install') is not None)

    def test_removal_regex(self):
        """"""
        for line in INSTALL_LOG.splitlines():
            match = re.search(server.non_ui_views.INSTALL_PATTERN, line)
            if match.group('removal'):
                self.assertTrue(match is not None)
                for key in ('date', 'removal', 'removal_name', 'status'):
                    self.assertTrue(match.group(key) is not None)


INSTALL_LOG = '''\
    Feb 12 2018 06:03:49 -0800 Install of Python 3-3.6.2: SUCCESSFUL
    Feb 12 2018 06:05:23 -0800 Install of DisableOSUpdateNotifications-1.0.0-1.0.0: SUCCESSFUL
    Feb 12 2018 06:07:07 -0800 Install of sas-root-cert-1.0.0-1.0.0: SUCCESSFUL
    Feb 13 2018 12:56:57 -0500 Removal of Blue Jeans Scheduler for Mac: SUCCESSFUL
    Feb 12 2018 06:07:07 -0800 Removal of sas-root-cert: SUCCESSFUL
    Feb 15 2018 11:31:30 -0500 Apple Software Update install of MRTConfigData-1.29: FAILED for unknown reason
    Feb 21 2018 10:17:59 -0500 Apple Software Update install of macOS High Sierra 10.13.3 Supplemental Update- : FAILED for unknown reason
    Mar 28 2018 12:58:50 -0400 Apple Software Update install of Command Line Tools (macOS High Sierra version 10.13) for Xcode-9.2: FAILED for unknown reason'''
