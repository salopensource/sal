"""General functional tests for the API endpoints."""


from api.v2.tests.tools import SalAPITestCase, TestGeneratorMeta


# pylint: disable=missing-docstring


class BusinessUnitTest(SalAPITestCase, metaclass=TestGeneratorMeta):
    setup_data = ['create_business_unit_data']
    tests = ['businessunit']


class ConditionTest(SalAPITestCase, metaclass=TestGeneratorMeta):
    fixtures = [
        'business_unit_fixtures.json', 'machine_group_fixtures.json',
        'machine_fixtures.json', 'conditions_fixture.json']
    tests = ['condition']


class FactTest(SalAPITestCase, metaclass=TestGeneratorMeta):
    fixtures = [
        'business_unit_fixtures.json', 'machine_group_fixtures.json',
        'machine_fixtures.json', 'fact_fixtures.json']
    tests = ['fact']


class InventoryTest(SalAPITestCase, metaclass=TestGeneratorMeta):
    fixtures = [
        'business_unit_fixtures.json', 'machine_group_fixtures.json',
        'machine_fixtures.json', 'inventory_fixtures.json']
    tests = ['inventoryitem']


class MachineGroupTest(SalAPITestCase, metaclass=TestGeneratorMeta):
    setup_data = ['create_machine_data']
    tests = ['machinegroup']


class PendingAppleUpdateTest(SalAPITestCase, metaclass=TestGeneratorMeta):
    fixtures = [
        'business_unit_fixtures.json', 'machine_group_fixtures.json',
        'machine_fixtures.json', 'pending_apple_update_fixtures.json']
    tests = ['pendingappleupdate']


class PendingUpdateTest(SalAPITestCase, metaclass=TestGeneratorMeta):
    fixtures = [
        'business_unit_fixtures.json', 'machine_group_fixtures.json',
        'machine_fixtures.json', 'pending_update_fixtures.json']
    tests = ['pendingupdate']


class PluginScriptTest(SalAPITestCase, metaclass=TestGeneratorMeta):
    fixtures = [
        'business_unit_fixtures.json', 'machine_group_fixtures.json',
        'machine_fixtures.json', 'plugin_script_fixtures.json']
    tests = ['pluginscriptrow']
