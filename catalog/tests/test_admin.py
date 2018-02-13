"""General functional tests for the catalog admin endpoints."""


from sal.test_utils import AdminTestCase


class CatalogAdminTest(AdminTestCase):
    """Test the admin site is configured to have all expected views."""
    admin_endpoints = {'catalog'}
