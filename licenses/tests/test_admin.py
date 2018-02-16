"""General functional tests for the license admin endpoints."""


from sal.test_utils import AdminTestCase


class LicenseAdminTest(AdminTestCase):
    """Test the admin site is configured to have all expected views."""
    admin_endpoints = {'license'}
