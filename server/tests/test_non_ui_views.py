"""Beginning of the test setup for non_ui_views"""


import base64
from unittest.mock import patch

from django.conf import settings
from django.http.response import Http404
from django.test import TestCase, Client

from server.models import MachineGroup, Machine
from server import non_ui_views


class CheckinDataTest(TestCase):
    """Test client checkins are resiliant."""

    fixtures = ['machine_group_fixture.json', 'business_unit_fixture.json', 'machine_fixture.json']

    def setUp(self):
        settings.BASIC_AUTH = False
        self.client = Client()
        self.content_type = 'content-type application/x-www-form-urlencoded'

    def test_checkin_requires_key_auth(self):
        """Ensure that key auth is enforced."""
        settings.BASIC_AUTH = True
        response = self.client.post('/checkin/', data={})
        self.assertEqual(response.status_code, 401)

    def test_checkin_data_empty(self):
        """Ensure that checkins with missing data get a 404 response."""
        response = self.client.post('/checkin/', data={}, content_type=self.content_type)
        self.assertEqual(response.status_code, 404)

    def test_checkin_incorrect_content_type(self):
        """Ensure checkin only accepts form encoded data."""
        response = self.client.post(
            '/checkin/', data={'serial': 'C0DEADBEEF'}, content_type='text/xml')
        # Should return 404 when looking up the machine's serial
        # number, which should be absent when sent with the wrong
        # content_type.
        self.assertEqual(response.status_code, 404)

    def test_vmware_serial(self):
        """Ensure serial translation for crazy VMWare serials works."""
        machine = non_ui_views.process_checkin_serial('+/c0deadbEEF')
        self.assertEqual(machine.serial, 'C0DEADBEEF')

    def test_machine_from_valid_serial(self):
        """Ensure we can get an existing Machine object."""
        machine = non_ui_views.process_checkin_serial('C0DEADBEEF')
        self.assertEqual(machine.pk, 1)

    def test_add_new_machine(self):
        """Ensure we can add a new machine with ADD_NEW_MACHINES=True"""
        machine = non_ui_views.process_checkin_serial('NotInDB')
        self.assertEqual(machine.pk, None)

    def test_no_add_new_machine(self):
        """Ensure 404 is raised when no ADD_NEW_MACHINES."""
        settings.ADD_NEW_MACHINES = False
        self.assertRaises(Http404, non_ui_views.process_checkin_serial, 'NotInDB')

    def test_get_checkin_machine_group(self):
        """Test basic function."""
        group = MachineGroup.objects.get(pk=1)
        self.assertEqual(non_ui_views.get_checkin_machine_group(group.key), group)

    def test_get_checkin_machine_group_bad_key(self):
        """Test basic function."""
        self.assertRaises(Http404, non_ui_views.get_checkin_machine_group, 'NotInDB')

    def test_get_checkin_machine_group_default(self):
        """Test basic function."""
        group = MachineGroup.objects.get(pk=1)
        settings.DEFAULT_MACHINE_GROUP_KEY = group.key
        self.assertEqual(non_ui_views.get_checkin_machine_group(None), group)

    def test_bad_report_data_type(self):
        """Test basic function."""
        response = self.client.post(
            '/checkin/', data={'serial': 'C0DEADBEEF', 'name': 1.0})
        self.assertEqual(response.status_code, 200)

    def test_deployed_on_checkin(self):
        """Test that a machine's deployed bool gets toggled."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        machine.deployed = False
        settings.DEPLOYED_ON_CHECKIN = True
        response = self.client.post(
            '/checkin/', data={'serial': machine.serial, 'key': machine.machine_group.key})
        machine.refresh_from_db()
        self.assertTrue(machine.deployed)

    def test_not_deployed_on_checkin(self):
        """Test that a machine's deployed bool is not updated on checkin."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        machine.deployed = False
        response = self.client.post(
            '/checkin/', data={'serial': machine.serial, 'key': machine.machine_group.key})
        machine.refresh_from_db()
        self.assertFalse(machine.deployed)

    def test_broken_client_checkin(self):
        """Test that a machine's deployed bool is not updated on checkin."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data= {
            'serial': machine.serial,
            'key': machine.machine_group.key,
            'broken_client': 'True'}
        response = self.client.post('/checkin/', data=data)
        machine.refresh_from_db()
        self.assertTrue(machine.broken_client)

    def test_get_console_user(self):
        user = 'Snake Plisskin'
        report = {'ConsoleUser': user}
        self.assertTrue(non_ui_views.get_console_user(report), user)
        report = {'username': user}
        self.assertTrue(non_ui_views.get_console_user(report), user)
        self.assertEqual(non_ui_views.get_console_user({}), None)


class MiscTest(TestCase):
    def test_checkin_memory_value_conversion(self):
        """Ensure conversion of memory to memory_kb is correct"""

        # hash of string description to number of KB
        memconv = {'4 GB': 4194304,
                   '8 GB': 8388608,
                   '1 TB': 1073741824}

        # pass each value and check proper value returned
        test_machine = Machine(serial='testtesttest123')
        for key in memconv:
            test_machine.memory = key
            self.assertEqual(non_ui_views.process_memory(test_machine), memconv[key])
