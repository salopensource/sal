from sal.test_utils import AdminTestCase


class ProfileAdminTest(AdminTestCase):
    """Test the admin site is configured to have all expected views."""
    admin_endpoints = {'profile', 'payload'}
