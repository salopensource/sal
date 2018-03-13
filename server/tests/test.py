"""General functional tests for the server app."""


from django.test import TestCase

import sal.plugin
from server import text_utils
from server import utils
from server.models import *


class UtilsTest(TestCase):
    """Test the Utilities module."""

    def test_listify_basic(self):
        """Ensure non-collection condition data is only str converted."""
        # Unicode
        catalogs = u'testing'
        result = text_utils.stringify(catalogs)
        self.assertEqual(result, catalogs)
        # TODO: Py3 will change this, as str = unicode in py2. Also, the
        # only current clients of stringify encode unicode
        # prior to ORM object creation. If we can't store unicode in the
        # db, then we can encode here. But really we should be able to
        # store unicode and let Django do the work of encoding it when
        # needed for output.
        self.assertTrue(isinstance(result, str))

        # str
        catalogs = 'testing'
        self.assertEqual(text_utils.stringify(catalogs), catalogs)

        # Bool, int, float, dict
        tests = (False, 5, 5.0, {'a': 'test'})
        for test in tests:
            self.assertEqual(text_utils.stringify(test), str(test))

    def test_listify_list(self):
        """Ensure condition list data can be converted to strings."""
        catalogs = ['testing', 'phase', 'production']
        result = text_utils.stringify(catalogs)
        self.assertEqual(result, ', '.join(catalogs))

    def test_listify_dict(self):
        """Ensure dict condition data can be converted to strings."""
        catalogs = ['testing', 'phase', {'key': 'value'}]
        result = text_utils.stringify(catalogs)
        self.assertEqual(result, "testing, phase, {'key': 'value'}")

    def test_listify_non_str_types(self):
        """Ensure nested non-str types are converted."""
        catalogs = [5, 5.0, {'a': 'test'}]
        result = text_utils.stringify(catalogs)
        self.assertEqual(result, "5, 5.0, {'a': 'test'}")


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
