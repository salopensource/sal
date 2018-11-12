"""Beginning of the test setup for non_ui_views"""


import base64
from unittest.mock import patch

from django.conf import settings
from django.http.response import Http404
from django.test import TestCase, Client

from server.models import *
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

