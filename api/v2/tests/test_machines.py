"""Tests for the machines API endpoints."""


from django.urls import reverse

from rest_framework import status

from api.v2.tests.tools import SalAPITestCase


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
