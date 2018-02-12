"""General functional tests for the API endpoints."""


from django.test import TestCase, Client
# from django.urls import reverse

from rest_framework import status

from server.models import ApiKey, User
# from api.v2.tests.tools import SalAPITestCase


class AdminTest(TestCase):
    """Test the admin site is configured to have all expected views."""
    admin_endpoints = {
        'apikey', 'businessunit', 'condition', 'fact', 'historicalfact',
        'installedupdate', 'machinedetailplugin', 'machinegroup', 'machine',
        'pendingappleupdate', 'pendingupdate', 'pluginscriptrow',
        'pluginscriptsubmission', 'plugin', 'report', 'salsetting', 'updatehistoryitem',
        'updatehistory', 'userprofile'}

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username='test')

    def test_no_access(self):
        """Test that unauthenticated requests redirected to login."""
        for path in self.admin_endpoints:
            response = self.client.get('/admin/server/{}'.format(path))
            # Redirect to login page.
            self.assertEqual(response.status_code, status.HTTP_301_MOVED_PERMANENTLY)

    def test_ro_access(self):
        """Test that ro requests are rejected.

        RO users should not have access to the admin site (unless they have
        `is_staff = True`.
        """
        self.user.user_profile = 'RO'
        self.user.save()
        self.client.force_login(self.user)

        for path in self.admin_endpoints:
            url = '/admin/server/{}/'.format(path)
            response = self.client.get(url)
            msg = 'Failed for path: "{}"'.format(path)
            self.assertEqual(response.status_code, status.HTTP_302_FOUND, msg=msg)
            self.assertEqual(response.url, '/admin/login/?next=/admin/server/{}/'.format(path),
                             msg=msg)

    def test_ga_access(self):
        """Ensure GA userprofile grants admin page access."""
        self.user.user_profile = 'GA'
        self.user.save()
        self.client.force_login(self.user)

        for path in self.admin_endpoints:
            url = '/admin/server/{}/'.format(path)
            response = self.client.get(url, follow=True)
            msg = 'Failed for path: "{}"'.format(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK, msg=msg)
