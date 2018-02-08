"""General functional tests for the server app."""


from django.test import TestCase

from server import utils


class UtilsTest(TestCase):
    """Test the Utilities module."""

    def test_listify_basic(self):
        """Ensure non-collection condition data is only str converted."""
        # Unicode
        catalogs = u'testing'
        result = utils.listify_condition_data(catalogs)
        self.assertEqual(result, catalogs)
        # TODO: Py3 will change this, as str = unicode in py2. Also, the
        # only current clients of listify_condition_data encode unicode
        # prior to ORM object creation. If we can't store unicode in the
        # db, then we can encode here. But really we should be able to
        # store unicode and let Django do the work of encoding it when
        # needed for output.
        self.assertTrue(isinstance(result, str))

        # str
        catalogs = 'testing'
        self.assertEqual(utils.listify_condition_data(catalogs), catalogs)

        # Bool, int, float, dict
        tests = (False, 5, 5.0, {'a': 'test'})
        for test in tests:
            self.assertEqual(utils.listify_condition_data(test), str(test))

    def test_listify_list(self):
        """Ensure condition list data can be converted to strings."""
        catalogs = ['testing', 'phase', 'production']
        result = utils.listify_condition_data(catalogs)
        self.assertEqual(result, ', '.join(catalogs))

    def test_listify_dict(self):
        """Ensure dict condition data can be converted to strings."""
        catalogs = ['testing', 'phase', {'key': 'value'}]
        result = utils.listify_condition_data(catalogs)
        self.assertEqual(result, "testing, phase, {'key': 'value'}")

    def test_listify_non_str_types(self):
        """Ensure nested non-str types are converted."""
        catalogs = [5, 5.0, {'a': 'test'}]
        result = utils.listify_condition_data(catalogs)
        self.assertEqual(result, "5, 5.0, {'a': 'test'}")
