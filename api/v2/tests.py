import contextlib
import cStringIO
import sys

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from search.models import *
from server.models import *


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

@contextlib.contextmanager
def nostdout(self):
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

    def create_machine_data(self):
        bu = BusinessUnit.objects.create(name='test')
        mg = MachineGroup.objects.create(name='test', business_unit=bu)
        Machine.objects.create(serial='C0DEADBEEF', machine_group=mg)

    def authed_get(self, name, args=None, params={}):
        url = reverse(name, args=args) if args else reverse(name)

        return self.client.get(url, params, **self.headers)


class MachinesTest(SalAPITestCase):
    setup_data = ['create_machine_data']


    def test_access(self):
        response = self.client.get(reverse('machine-list'))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['content-type'], 'application/json')

    def test_get_returns_json_200(self):
        response = self.authed_get('machine-list')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')

    def test_detail_by_serial(self):
        response = self.authed_get('machine-detail', args=('C0DEADBEEF',))
        self.assertEqual(response.status_code, 200)

    def test_detail_by_id_returns_404(self):
        response = self.authed_get('machine-detail', args=(1,))
        self.assertEqual(response.status_code, 404)

    def test_list_with_full(self):
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
        response = self.authed_get(
            'machine-detail', args=('C0DEADBEEF',),
            params= {'fields': 'activity', 'fields!': 'hostname' })
        self.assertIn('activity', response.data)
        self.assertNotIn('hostname', response.data)

    def test_list_include_fields(self):
        response = self.authed_get(
            'machine-list',
            params={'fields': 'activity', 'fields!': 'hostname' })
        record = response.data['results'][0]
        self.assertIn('activity', record)
        self.assertNotIn('hostname', record)


class SavedSearchTest(SalAPITestCase):
    fixtures = ['search_fixtures.json', 'user_fixture.json']
    setup_data = ['create_machine_data']

    def test_list(self):
        response = self.authed_get('savedsearch-list')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertTrue(len(response.data['results']) == 1)

    def test_detail(self):
        response = self.authed_get('savedsearch-detail', args=(3,))
        self.assertEqual(response.status_code, 200)
        self.assertIn('search_groups', response.data)
        self.assertIn('search_rows', response.data['search_groups'][0])

    @nostdout
    def test_execute(self):
        response = self.authed_get(
            'savedsearch-execute', args=(3,))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        # TODO: Set up a search that only gets 1 of 2 computers.

    @nostdout
    def test_full_param(self):
        # Test a "regular" savedsearch and make sure it has the
        # abbreviated keys only.
        response = self.authed_get('savedsearch-execute', args=(3,))
        keys = response.data[0].keys()

        self.assertTrue(all(k in keys for k in SEARCH_RESULT_MACHINE_COLUMNS))
        self.assertFalse(any(k in keys for k in ALL_MACHINE_COLUMNS))

        # Now test one that uses full and make sure it has the extra
        # keys.
        response = self.authed_get(
            'savedsearch-execute', args=(3,), params={'full': None})
        keys = response.data[0].keys()

        self.assertTrue(
            all(k in keys for k in ALL_MACHINE_COLUMNS))
