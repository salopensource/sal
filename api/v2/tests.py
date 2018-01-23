"""Tests for the Sal API app."""


import contextlib
import cStringIO
import sys

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from server.models import (ApiKey, BusinessUnit, MachineGroup, Machine)


ALL_MACHINE_COLUMNS = {
    'console_user', 'munki_version', 'hd_space', 'machine_model', 'cpu_speed',
    'serial', 'id', 'last_puppet_run', 'errors', 'puppet_version', 'hostname',
    'puppet_errors', 'machine_model_friendly', 'memory', 'memory_kb',
    'warnings', 'install_log', 'first_checkin', 'last_checkin',
    'broken_client', 'hd_total', 'os_family', 'report', 'deployed',
    'operating_system', 'report_format', 'machine_group', 'sal_version',
    'manifest', 'hd_percent', 'cpu_type', 'activity', 'install_log_hash'}
REMOVED_MACHINE_COLUMNS = {
    'activity', 'report', 'install_log', 'install_log_hash'}
SEARCH_RESULT_MACHINE_COLUMNS = {
    'id', 'serial', 'hostname', 'console_user', 'last_checkin'}


# Get rid of pylint complaining about Django ORM stuff
# pylint: disable=no-member


@contextlib.contextmanager
def no_stdout():
    """Method decorator to prevent stdout from mucking up test output"""
    saved_stdout = sys.stdout
    sys.stdout = cStringIO.StringIO()
    try:
        yield
    except Exception:
        saved_output = sys.stdout
        sys.stdout = saved_stdout
        print saved_output.getvalue()
        raise
    sys.stdout = saved_stdout


class SalAPITestCase(APITestCase):
    """Overriden DRF TestCase to simplify data setup and authenticated
    request generation.
    """
    setup_data = []

    def setUp(self):
        # Set up an APIKey for authenticated tests to use.
        api_key = ApiKey.objects.create()
        self.headers = {
            'HTTP_PRIVATEKEY': api_key.private_key,
            'HTTP_PUBLICKEY': api_key.public_key}

        for data_method_name in self.setup_data:
            data_method = getattr(self, data_method_name)
            data_method()

    # pylint: disable=no-self-use
    def create_machine_data(self):
        """Created all data needed for machine testing."""
        business_unit = BusinessUnit.objects.create(name='test')
        machine_group = MachineGroup.objects.create(
            name='test', business_unit=business_unit)
        Machine.objects.create(
            serial='C0DEADBEEF', machine_group=machine_group)
        Machine.objects.create(
            serial='C1DEADBEEF', machine_group=machine_group)

    def authed_get(self, name, args=None, params=None):
        """Perform an authenticated get request to API."""
        if not params:
            params = {}
        url = reverse(name, args=args) if args else reverse(name)

        return self.client.get(url, params, **self.headers)


class MachinesTest(SalAPITestCase):
    """Test the Machine endpoints."""
    setup_data = ['create_machine_data']


    def test_access(self):
        """Test that unauthenticated requests are rejected"""
        response = self.client.get(reverse('machine-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_content_type(self):
        """Test that all responses return JSON."""
        response = self.client.get(reverse('machine-list'))
        self.assertEqual(response['content-type'], 'application/json')
        response = self.authed_get('machine-list')
        self.assertEqual(response['content-type'], 'application/json')

    def test_get_returns_json_200(self):
        """Test that a pretty generic API request returns 200/OK"""
        response = self.authed_get('machine-list')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')

    def test_detail_by_serial(self):
        """Test that machines can be requested by SN"""
        response = self.authed_get('machine-detail', args=('C0DEADBEEF',))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_by_id_returns_404(self):
        """Test that machines cannot requested by ID/PK"""
        response = self.authed_get('machine-detail', args=(1,))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_with_full(self):
        """Test machine list endpoint with `full` param returns more"""
        response = self.authed_get('machine-list')
        full_response = self.authed_get(
            'machine-list', params={'full': None})

        self.assertNotEqual(response.data, full_response.data)
        # Make sure "regular" machine response has removed the expected
        # keys.
        self.assertFalse(any(
            k in response.data['results'][0] for k in REMOVED_MACHINE_COLUMNS))
        self.assertTrue(all(
            k in response.data['results'][0] for
            k in ALL_MACHINE_COLUMNS - REMOVED_MACHINE_COLUMNS))
        # ...and that a "full" machine response includes them.
        self.assertTrue(all(
            k in full_response.data['results'][0] for
            k in ALL_MACHINE_COLUMNS))

    def test_detail_with_full(self):
        """Test machine detail endpoint with `full` param returns more"""
        response = self.authed_get('machine-detail', args=('C0DEADBEEF',))
        full_response = self.authed_get(
            'machine-detail', args=('C0DEADBEEF',), params={'full': None})

        self.assertNotEqual(response.data, full_response.data)
        # Make sure "regular" machine response has removed the expected
        # keys.
        self.assertFalse(any(
            k in response.data for k in REMOVED_MACHINE_COLUMNS))
        self.assertTrue(all(
            k in response.data for
            k in ALL_MACHINE_COLUMNS - REMOVED_MACHINE_COLUMNS))
        # ...and that a "full" machine response includes them.
        self.assertTrue(all(
            k in full_response.data for k in ALL_MACHINE_COLUMNS))

    def test_detail_include_fields(self):
        """Test the field inclusion/exclusion params for detail."""
        response = self.authed_get(
            'machine-detail', args=('C0DEADBEEF',),
            params={'fields': 'activity', 'fields!': 'hostname'})
        self.assertIn('activity', response.data)
        self.assertNotIn('hostname', response.data)

    def test_list_include_fields(self):
        """Test the field inclusion/exclusion params for list."""
        response = self.authed_get(
            'machine-list',
            params={'fields': 'activity', 'fields!': 'hostname'})
        record = response.data['results'][0]
        self.assertIn('activity', record)
        self.assertNotIn('hostname', record)


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
