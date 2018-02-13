"""General functional tests for the search admin endpoints."""


from sal.test_utils import AdminTestCase


class SearchAdminTest(AdminTestCase):
    """Test the admin site is configured to have all expected views."""
    admin_endpoints = {'savedsearch', 'searchgroup', 'searchrow', 'searchfieldcache',
                       'searchcache'}
