"""General functional tests for the text_utils module."""


from django.test import TestCase

from utils import text_utils


class TextUtilsTest(TestCase):
    """Test the Utilities module."""

    def test_safe_text_null(self):
        """Ensure that null characters are dropped."""
        original = '\x00'
        self.assertTrue(text_utils.safe_text(original) == '')
        self.assertTrue(text_utils.safe_text(original.encode() == ''))

    def test_listify_basic(self):
        """Ensure non-collection condition data is only str converted."""
        catalogs = 'testing'
        result = text_utils.stringify(catalogs)
        self.assertEqual(result, catalogs)
        self.assertTrue(isinstance(result, str))

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
