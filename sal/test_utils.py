"""Reusable testing components"""


from django.test import TestCase, Client
from django.urls import reverse

from rest_framework import status

from server.models import User


class AdminTestCase(TestCase):
    """Test the admin site is configured to have all expected views."""
    admin_endpoints = {}

    def app(self):
        """Return the app name, which is the base of the module."""
        return self.__module__.split('.')[0]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username='test')

    def test_no_access(self):
        """Test that unauthenticated requests redirected to login."""
        for path in self.admin_endpoints:
            url = reverse('admin:{}_{}_changelist'.format(self.app(), path))
            response = self.client.get(url)
            # Redirect to login page.
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
            self.assertEqual(response.url, '{}?next={}'.format(reverse('admin:login'), url))

    def test_ro_access(self):
        """Test that ro requests are rejected.

        RO users should not have access to the admin site (unless they have
        `is_staff = True`.
        """
        self.user.user_profile = 'RO'
        self.user.save()
        self.client.force_login(self.user)

        for path in self.admin_endpoints:
            url = reverse('admin:{}_{}_changelist'.format(self.app(), path))
            response = self.client.get(url)
            msg = 'Failed for path: "{}"'.format(path)
            self.assertEqual(response.status_code, status.HTTP_302_FOUND, msg=msg)
            self.assertEqual(response.url, '{}?next={}'.format(reverse('admin:login'), url),
                             msg=msg)

    def test_ga_access(self):
        """Ensure GA userprofile grants admin page access."""
        self.user.user_profile = 'GA'
        self.user.save()
        self.client.force_login(self.user)

        for path in self.admin_endpoints:
            url = reverse('admin:{}_{}_changelist'.format(self.app(), path))
            response = self.client.get(url, follow=True)
            msg = 'Failed for path: "{}"'.format(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK, msg=msg)
