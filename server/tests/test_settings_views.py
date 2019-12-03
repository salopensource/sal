"""Beginning of the test setup for non_ui_views"""


from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, Client

import server.utils
from sal.plugin import Widget, ReportPlugin, DetailPlugin
from server.models import Plugin, Report, MachineDetailPlugin


class WidgetSettingsTest(TestCase):
    """Functional tests for Widget settings views."""
    fixtures = ['user_fixture.json']

    def setUp(self):
        self.ga_user = User.objects.get(pk=1)
        user_profile = self.ga_user.userprofile
        user_profile.level = 'GA'
        user_profile.save()
        settings.BASIC_AUTH = False
        self.client = Client()
        self.client.force_login(self.ga_user)
        self.url = '/settings/plugins/enable'
        # Avoid sending analytics to the project while testing!
        server.utils.set_setting('send_data', False)
        self.widget = Plugin(name='Widget', order=0)
        self.widget.save()
        self.report_plugin = Report(name='Report')
        self.report_plugin.save()

    def test_enable_enabled_widget(self):
        """Test that enabling an enabled widget does nothing"""
        self.client.get(f'{self.url}/{self.widget.name}/')
        self.assertEqual(Plugin.objects.count(), 1)

    @patch('sal.plugin.PluginManager.get_plugin_by_name')
    def test_enable_disabled_widget(self, manager):
        """Test that enabling a disabled widget works"""
        # Fake that this plugin has a yapsy file
        manager.return_value = Widget()
        self.client.get(f'{self.url}/tacos/')
        self.assertEqual(Plugin.objects.count(), 2)

    def test_enable_nonexistent_widget(self):
        """If a plugin does not exist, redirect to plugin list."""
        self.client.get(f'{self.url}/tacos/')
        self.assertEqual(Plugin.objects.count(), 1)


class DetailPluginSettingsTest(TestCase):
    """Functional tests for DetailPlugin settings views."""
    fixtures = ['user_fixture.json']

    def setUp(self):
        self.ga_user = User.objects.get(pk=1)
        user_profile = self.ga_user.userprofile
        user_profile.level = 'GA'
        user_profile.save()
        settings.BASIC_AUTH = False
        self.client = Client()
        self.client.force_login(self.ga_user)
        self.url = '/settings/plugins/machinedetail/enable'
        # Avoid sending analytics to the project while testing!
        server.utils.set_setting('send_data', False)

    def test_enable_enabled_detail_plugin(self):
        """Test that enabling an enabled plugin does nothing"""
        self.client.get(f'{self.url}/MachineDetailSecurity/')
        self.assertEqual(MachineDetailPlugin.objects.count(), 1)

    @patch('sal.plugin.PluginManager.get_plugin_by_name')
    def test_enable_disabled_detail_plugin(self, manager):
        """Test that enabling a disabled detail plugin works"""
        # Fake that this plugin has a yapsy file
        manager.return_value = DetailPlugin()
        self.client.get(f'{self.url}/tacos/')
        self.assertEqual(MachineDetailPlugin.objects.count(), 2)

    def test_enable_nonexistent_detail_plugin(self):
        """If a plugin does not exist, redirect to plugin list."""
        self.client.get(f'{self.url}/tacos/')
        self.assertEqual(MachineDetailPlugin.objects.count(), 1)


class ReportSettingsTest(TestCase):
    """Functional tests for Report settings views."""
    fixtures = ['user_fixture.json']

    def setUp(self):
        self.ga_user = User.objects.get(pk=1)
        user_profile = self.ga_user.userprofile
        user_profile.level = 'GA'
        user_profile.save()
        settings.BASIC_AUTH = False
        self.client = Client()
        self.client.force_login(self.ga_user)
        self.url = '/settings/plugins/reports/enable'
        # Avoid sending analytics to the project while testing!
        server.utils.set_setting('send_data', False)

    def test_enable_enabled_report(self):
        """Test that enabling an enabled report does nothing"""
        self.client.get(f'{self.url}/InstallReport/')
        # There are two included by default.
        self.assertEqual(Report.objects.count(), 2)

    @patch('sal.plugin.PluginManager.get_plugin_by_name')
    def test_enable_disabled_report(self, manager):
        """Test that enabling a disabled report works"""
        # Fake that this plugin has a yapsy file
        manager.return_value = ReportPlugin()
        self.client.get(f'{self.url}/tacos/')
        # breakpoint()
        self.assertEqual(Report.objects.count(), 3)

    def test_enable_nonexistent_report(self):
        """If a plugin does not exist, redirect to plugin list."""
        self.client.get(f'{self.url}/tacos/')
        # There are two included by default.
        self.assertEqual(Report.objects.count(), 2)
