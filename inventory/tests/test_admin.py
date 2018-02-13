"""General functional tests for the inventory admin endpoints."""


from sal.test_utils import AdminTestCase


class InventoryAdminTest(AdminTestCase):
    """Test the admin site is configured to have all expected views."""
    admin_endpoints = {'application', 'inventory', 'inventoryitem'}
