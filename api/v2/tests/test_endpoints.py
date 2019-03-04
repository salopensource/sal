"""General functional tests for the API endpoints."""


from api.v2.tests.tools import SalAPITestCase, TestGeneratorMeta


# pylint: disable=missing-docstring


class BusinessUnitTest(SalAPITestCase, metaclass=TestGeneratorMeta):
    setup_data = ['create_business_unit_data']
    tests = ['businessunit']


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


class PluginScriptTest(SalAPITestCase, metaclass=TestGeneratorMeta):
    fixtures = [
        'business_unit_fixtures.json', 'machine_group_fixtures.json',
        'machine_fixtures.json', 'plugin_script_fixtures.json']
    tests = ['pluginscriptrow']
