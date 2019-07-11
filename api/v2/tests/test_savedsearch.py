"""Tests for the Sal API app."""


from rest_framework import status

from api.v2.tests.tools import SalAPITestCase, no_stdout
from api.v2.tests.test_machines import ALL_MACHINE_COLUMNS

SEARCH_RESULT_MACHINE_COLUMNS = {'id', 'serial', 'hostname', 'console_user', 'last_checkin'}


class SavedSearchTest(SalAPITestCase):
    """Tests covering the SavedSearch endpoint"""
    fixtures = ['search_fixtures.json', 'user_fixture.json']
    setup_data = ['create_machine_data']

    def test_list(self):
        """Test the listing endpoint and nested serialization."""
        response = self.authed_get('savedsearch-list')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertTrue(len(response.data['results']) == 2)
        # Test the nested search serializers.
        self.assertIn('search_groups', response.data['results'][0])
        self.assertIn(
            'search_rows', response.data['results'][0]['search_groups'][0])

    def test_detail(self):
        """Test the detail endpoint and nested serialization."""
        response = self.authed_get('savedsearch-detail', args=(3,))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test the nested search serializers.
        self.assertIn('search_groups', response.data)
        self.assertIn('search_rows', response.data['search_groups'][0])

    def test_execute(self):
        """Test saved search execution."""
        with no_stdout():
            response = self.authed_get(
                'savedsearch-execute', args=(2,))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_execute_filtered(self):
        """Test saved search execution results are filtering."""
        with no_stdout():
            response = self.authed_get(
                'savedsearch-execute', args=(3,))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_full_param(self):
        """Test saved search execution with the `full` param."""
        # Test a "regular" savedsearch and make sure it has the
        # abbreviated keys only.
        with no_stdout():
            response = self.authed_get('savedsearch-execute', args=(3,))
        keys = set(response.data[0].keys())

        self.assertEqual(keys, SEARCH_RESULT_MACHINE_COLUMNS)

        # Now test one that uses full and make sure it has the extra
        # keys.
        with no_stdout():
            response = self.authed_get(
                'savedsearch-execute', args=(3,), params={'full': None})
        keys = set(response.data[0].keys())

        self.assertEqual(keys, ALL_MACHINE_COLUMNS)
