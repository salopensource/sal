"""Tests for the machines API endpoints."""


from django.urls import reverse

from rest_framework import status

from api.v2.tests.tools import SalAPITestCase


ALL_MACHINE_COLUMNS = {
    'console_user', 'munki_version', 'hd_space', 'machine_model', 'cpu_speed', 'serial', 'id',
    'hostname', 'machine_model_friendly', 'memory', 'memory_kb', 'first_checkin', 'last_checkin',
    'broken_client', 'hd_total', 'os_family', 'deployed', 'operating_system', 'machine_group',
    'sal_version', 'manifest', 'hd_percent', 'cpu_type'}
REMOVED_MACHINE_COLUMNS = set()


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
