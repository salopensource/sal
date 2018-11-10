"""General functional tests for the server app."""


from django.test import TestCase

import sal.plugin
from server import utils
from server.models import Plugin


class PluginUtilsTest(TestCase):
    """Test the plugin utilities."""

    def test_remove_missing_plugins(self):
        """Ensure removed from disk are also removed from the DB."""
        Plugin.objects.create(name='Test', order=0)
        utils.reload_plugins_model()
        self.assertEqual(len(Plugin.objects.all()), 0)

    def test_default_plugin_load(self):
        """Ensure that no plugins result in a default loadout."""
        self.assertEqual(Plugin.objects.count(), 0)
        utils.load_default_plugins()
        self.assertNotEqual(Plugin.objects.count(), 0)
