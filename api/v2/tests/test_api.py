"""General functional tests for the API endpoints."""


from django.urls import reverse

from rest_framework import status

from api.v2.tests.tools import SalAPITestCase


class APITest(SalAPITestCase):
    """Test the API itself."""
    api_endpoints = {
        'business_units', 'conditions', 'facts', 'inventory', 'machine_groups',
        'machines', 'pending_apple_updates', 'pending_updates',
        'plugin_script_rows', 'saved_searches'}

    def test_access(self):
        """Test that unauthenticated requests are rejected"""
        response = self.client.get(reverse('api-root'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_options(self):
        """Ensure that API discovery is possible."""
        response = self.authed_options('api-root')
        self.assertIn('application/json', response.data['renders'])
        self.assertIn('application/json', response.data['parses'])
        self.assertIn('multipart/form-data', response.data['parses'])

    def test_api_root_get(self):
        """Test that all expected endpoints are present."""
        response = self.authed_get('api-root')
        self.assertEqual(self.api_endpoints, set(response.data.keys()))

    def test_api_docs(self):
        """Make sure the docs site is working."""
        response = self.authed_get('api-docs:docs-index')
        self.assertEqual(response['content-type'], 'text/html; charset=utf-8')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
