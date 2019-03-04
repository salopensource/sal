"""General functional tests for the Server admin."""


from sal.test_utils import AdminTestCase


class ServerAdminTest(AdminTestCase):
    """Test the admin site is configured to have all expected views."""
    admin_endpoints = {
        'apikey', 'businessunit', 'fact', 'historicalfact',
        'machinedetailplugin', 'machinegroup', 'machine', 'manageditem', 'managementsource',
        'pluginscriptrow', 'pluginscriptsubmission', 'plugin', 'report', 'salsetting',
        'updatehistoryitem', 'updatehistory'}
