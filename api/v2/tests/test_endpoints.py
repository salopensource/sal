"""General functional tests for the API endpoints."""


from api.v2.tests.tools import SalAPITestCase, TestGeneratorMeta


# pylint: disable=missing-docstring


class BusinessUnitTest(SalAPITestCase):
    __metaclass__ = TestGeneratorMeta
    setup_data = ['create_business_unit_data']
    tests = ['businessunit']


class ConditionTest(SalAPITestCase):
    __metaclass__ = TestGeneratorMeta
    fixtures = [
        'business_unit_fixtures.json', 'machine_group_fixtures.json',
        'machine_fixtures.json', 'conditions_fixture.json']
    tests = ['condition']


class FactTest(SalAPITestCase):
    __metaclass__ = TestGeneratorMeta
    fixtures = [
        'business_unit_fixtures.json', 'machine_group_fixtures.json',
        'machine_fixtures.json', 'fact_fixtures.json']
    tests = ['fact']


class InventoryTest(SalAPITestCase):
    __metaclass__ = TestGeneratorMeta
    fixtures = [
        'business_unit_fixtures.json', 'machine_group_fixtures.json',
        'machine_fixtures.json', 'inventory_fixtures.json']
    tests = ['inventoryitem']


class MachineGroupTest(SalAPITestCase):
    __metaclass__ = TestGeneratorMeta
    setup_data = ['create_machine_data']
    tests = ['machinegroup']


class PendingAppleUpdateTest(SalAPITestCase):
    __metaclass__ = TestGeneratorMeta
    fixtures = [
        'business_unit_fixtures.json', 'machine_group_fixtures.json',
        'machine_fixtures.json', 'pending_apple_update_fixtures.json']
    tests = ['pendingappleupdate']


class PendingUpdateTest(SalAPITestCase):
    __metaclass__ = TestGeneratorMeta
    fixtures = [
        'business_unit_fixtures.json', 'machine_group_fixtures.json',
        'machine_fixtures.json', 'pending_update_fixtures.json']
    tests = ['pendingupdate']


class PluginScriptTest(SalAPITestCase):
    __metaclass__ = TestGeneratorMeta
    fixtures = [
        'business_unit_fixtures.json', 'machine_group_fixtures.json',
        'machine_fixtures.json', 'plugin_script_fixtures.json']
    tests = ['pluginscriptrow']
