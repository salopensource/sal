import contextlib
import cStringIO
import itertools
import sys

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from search.models import *
from server.models import *


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

    def test_get_by_serial(self):
        response = self.authed_get('machine-detail', args=('C0DEADBEEF',))
        self.assertEqual(response.status_code, 200)

    def test_get_by_id_returns_404(self):
        response = self.authed_get('machine-detail', args=(1,))
        self.assertEqual(response.status_code, 404)

    def test_get_with_full(self):
        response = self.authed_get('machine-detail', args=('C0DEADBEEF',))
        full_response = self.authed_get(
            'machine-detail', args=('C0DEADBEEF',), params={'full': None})

        short, full = response.json(), full_response.json()
        self.assertNotEqual(len(short), len(full))
        self.assertTrue('activity' in full)
        self.assertFalse('activity' in short)

    def test_include_fields(self):
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
        abbrev_keys = (
            'id', 'serial', 'hostname', 'console_user', 'last_checkin')
        full_keys = (
            'operating_system', 'memory', 'memory_kb', 'munki_version',
            'manifest', 'hd_space', 'hd_total', 'hd_percent', 'machine_model',
            'machine_model_friendly', 'cpu_type', 'cpu_speed', 'os_family',
            'first_checkin', 'report', 'report_format', 'errors', 'warnings',
            'activity', 'puppet_version', 'sal_version', 'last_puppet_run',
            'puppet_errors', 'install_log_hash', 'install_log', 'deployed',
            'broken_client', 'machine_group')
        response = self.authed_get('savedsearch-execute', args=(3,))
        keys = response.data[0].keys()

        self.assertTrue(all(k in keys for k in abbrev_keys))
        self.assertFalse(any(k in keys for k in extended_keys))

        response = self.authed_get(
            'savedsearch-execute', args=(3,), params={'full': None})
        keys = response.data[0].keys()

        self.assertTrue(
            all(k in keys for k in itertools.chain(abbrev_keys, full_keys)))
