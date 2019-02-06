"""Beginning of the test setup for non_ui_views"""


import base64
import bz2
import datetime
import dateutil
import json
import plistlib
import pytz
from unittest.mock import patch

from django.conf import settings
from django.http.response import Http404
from django.test import TestCase, Client
from django.utils.timezone import now

import server.utils
from server import non_ui_views
from server.models import (
    MachineGroup, Machine, ManagementSource, ManagedItem, Fact, HistoricalFact, PendingAppleUpdate,
    UpdateHistory, UpdateHistoryItem)


class CheckinDataTest(TestCase):
    """Functional tests for client checkins."""

    fixtures = ['machine_group_fixture.json', 'business_unit_fixture.json', 'machine_fixture.json']

    def setUp(self):
        settings.BASIC_AUTH = False
        self.client = Client()
        self.content_type = 'application/json'
        self.url = '/checkin/'
        # Avoid sending analytics to the project while testing!
        server.utils.set_setting('send_data', False)

    def test_checkin_requires_key_auth(self):
        """Ensure that key auth is enforced."""
        settings.BASIC_AUTH = True
        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, 401)

    def test_checkin_data_empty(self):
        """Ensure that checkins with missing data get a 400 response."""
        response = self.client.post(self.url, data=json.dumps({}), content_type=self.content_type)
        self.assertEqual(response.status_code, 400)

    def test_checkin_data_missing_required_machine_key(self):
        """Ensure that checkins with no machine dict get a 400 response."""
        response = self.client.post(self.url, data=json.dumps({}), content_type=self.content_type)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'Checkin JSON is missing required key "machine"!')

    def test_checkin_data_missing_required_serial_key(self):
        """Ensure that checkins with no machine dict get a 400 response."""
        response = self.client.post(
            self.url, data=json.dumps({'machine': {}}), content_type=self.content_type)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.content, b'Checkin JSON is missing required "machine" key "serial"!')

    def test_checkin_incorrect_content_type(self):
        """Ensure checkin only accepts JSON encoded data."""
        # Send a form-encoded request.
        response = self.client.post(self.url, data='', content_type='text/xml')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'Checkin must be content-type "application/json"!')

    def test_checkin_invalid_json(self):
        """Ensure fails for invalid JSON."""
        # Send a form-encoded request.
        response = self.client.post(
            self.url, data='this is not json', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'Checkin has invalid JSON!')

    def test_deployed_on_checkin(self):
        """Test that a machine's deployed bool gets toggled."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        machine.deployed = False
        machine.save()
        settings.DEPLOYED_ON_CHECKIN = True
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key}})
        self.client.post(self.url, data=data, content_type=self.content_type)
        machine.refresh_from_db()
        self.assertTrue(machine.deployed)

    def test_not_deployed_on_checkin(self):
        """Test that a machine's deployed bool is not updated on checkin."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        machine.deployed = False
        settings.DEPLOYED_ON_CHECKIN = False
        machine.save()
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key}})
        self.client.post(self.url, data=data, content_type=self.content_type)
        machine.refresh_from_db()
        self.assertFalse(machine.deployed)

    def test_new_machine_on_checkin(self):
        """Test that a machine gets created when it doesn't already exist."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        test_serial = 'New machine'.upper()
        settings.ADD_NEW_MACHINES = True
        data = json.dumps({
            'machine': {'serial': test_serial},
            'sal': {'key': machine.machine_group.key}})
        self.client.post(self.url, data=data, content_type=self.content_type)
        machine.refresh_from_db()
        self.assertTrue(Machine.objects.get(serial=test_serial))

    def test_no_new_machine_on_checkin(self):
        """Test that a machine doesn't get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        test_serial = 'New machine'.upper()
        settings.ADD_NEW_MACHINES = False
        data = json.dumps({
            'machine': {'serial': test_serial},
            'sal': {'key': machine.machine_group.key}})
        self.client.post(self.url, data=data, content_type=self.content_type)
        machine.refresh_from_db()
        self.assertRaises(Machine.DoesNotExist, Machine.objects.get, serial=test_serial)

    def test_broken_client_checkin(self):
        """Test that a machine's broken bool is updated on checkin."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key, 'broken_client': True}})
        response = self.client.post(self.url, data=data, content_type=self.content_type)
        machine.refresh_from_db()
        self.assertTrue(machine.broken_client)
        self.assertEqual(
            response.content, b'Broken Client report submmitted for %s' % machine.serial.encode())

    def test_minimal_data(self):
        """Test checkin can complete with bare minimum data."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key}})
        response = self.client.post(self.url, data, content_type=self.content_type)
        self.assertEqual(response.status_code, 200)

    def test_management_source_creation(self):
        """Test checkin creates management sources."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key},
            'munki': {}})
        self.client.post(self.url, data, content_type=self.content_type)
        self.assertTrue(ManagementSource.objects.filter(name='munki').exists())


class CheckinFactTest(TestCase):
    """Functional tests for client checkins for Fact/HistoricalFact."""

    fixtures = ['machine_group_fixture.json', 'business_unit_fixture.json', 'machine_fixture.json']

    def setUp(self):
        settings.BASIC_AUTH = False
        self.client = Client()
        self.content_type = 'application/json'
        self.url = '/checkin/'
        # Avoid sending analytics to the project while testing!
        server.utils.set_setting('send_data', False)

    def test_facts_cleanup(self):
        """Test that all of a machine's facts get dropped."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key}})
        self.client.post(self.url, data, content_type=self.content_type)
        self.assertEqual(Fact.objects.count(), 0)

    def test_facts_created(self):
        """Test that facts get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key},
            'munki': {'facts': {'test_user': 'Snake Plisskin'}}
        })
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        fact = machine.facts.get(fact_name='test_user')
        self.assertEqual(fact.fact_name, 'test_user')
        self.assertEqual(fact.fact_data, 'Snake Plisskin')
        self.assertEqual(fact.management_source.name, 'munki')

    @patch('server.non_ui_views.HISTORICAL_FACTS', ['test_user'])
    def test_historical_facts_created(self):
        """Test historical facts get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key},
            'munki': {'facts': {'test_user': 'Snake Plisskin'}}
        })
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        fact = machine.facts.get(fact_name='test_user')
        historical_fact = machine.historical_facts.get(fact_name='test_user')
        self.assertEqual(fact.fact_name, 'test_user')
        self.assertEqual(fact.fact_data, 'Snake Plisskin')
        self.assertEqual(fact.management_source.name, 'munki')
        self.assertEqual(historical_fact.fact_name, 'test_user')
        self.assertEqual(historical_fact.fact_data, 'Snake Plisskin')
        self.assertEqual(historical_fact.management_source.name, 'munki')

    @patch('server.non_ui_views.IGNORE_PREFIXES', ['ignore'])
    def test_ignore_facts_setting_works(self):
        """Test the ignore prefixes setting for facts works."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key},
            'munki': {'facts': {'test_user': 'Snake Plisskin', 'ignore_this': 'Yep'}}
        })
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        self.assertRaises(Fact.DoesNotExist, machine.facts.get, fact_name='ignore_this')


class CheckinManagedItemTest(TestCase):
    """Functional tests for client checkins for ManagedItem."""

    fixtures = ['machine_group_fixture.json', 'business_unit_fixture.json', 'machine_fixture.json']

    def setUp(self):
        settings.BASIC_AUTH = False
        self.client = Client()
        self.content_type = 'application/json'
        self.url = '/checkin/'
        # Avoid sending analytics to the project while testing!
        server.utils.set_setting('send_data', False)

    def test_managed_item_cleanup(self):
        """Test that all of a machine's managed items get dropped."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key}})
        self.client.post(self.url, data, content_type=self.content_type)
        self.assertEqual(ManagedItem.objects.count(), 0)

    def test_managed_item_created(self):
        """Test that managed items get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key},
            'munki': {'managed_items': {
                'Dwarf Fortress': {}}}})
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        managed_item = machine.manageditem_set.get(name='Dwarf Fortress')
        self.assertEqual(managed_item.name, 'Dwarf Fortress')
        self.assertEqual(managed_item.management_source.name, 'munki')

    @patch('django.utils.timezone.now')
    def test_managed_item_created_with_defaults(self, mock_now):
        """Test that managed items get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        mock_now.return_value = now()
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key},
            'munki': {'managed_items': {
                'Dwarf Fortress': {}}}})
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        managed_item = machine.manageditem_set.get(name='Dwarf Fortress')
        self.assertEqual(managed_item.name, 'Dwarf Fortress')
        self.assertEqual(managed_item.date_managed, mock_now.return_value)
        self.assertEqual(managed_item.status, 'UNKNOWN')
        self.assertEqual(managed_item.data, None)

    def test_managed_item_created_with_values(self):
        """Test that managed items get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key},
            'munki': {'managed_items': {
                'Dwarf Fortress': {
                    'date_managed': '2020-02-29T13:00:00Z',
                    'status': 'PRESENT',
                    'data': {'comment': '...and there was much rejoicing.'}},
                'Nethack': {
                    'date_managed': '2020-02-29T13:00:00Z',
                    'status': 'ABSENT',
                    'data': {'comment': '...and there was much rejoicing.'}}}}})
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        managed_item = machine.manageditem_set.get(name='Dwarf Fortress')
        self.assertEqual(managed_item.name, 'Dwarf Fortress')
        self.assertEqual(managed_item.date_managed, dateutil.parser.parse('2020-02-29T13:00:00Z'))
        self.assertEqual(managed_item.status, 'PRESENT')
        self.assertTrue('comment' in json.loads(managed_item.data).keys())
        managed_item = machine.manageditem_set.get(name='Nethack')
        self.assertEqual(managed_item.name, 'Nethack')
        self.assertEqual(managed_item.date_managed, dateutil.parser.parse('2020-02-29T13:00:00Z'))
        self.assertEqual(managed_item.status, 'ABSENT')
        self.assertTrue('comment' in json.loads(managed_item.data).keys())


class CheckinMunkiItemTest(TestCase):
    """Functional tests for client checkins for Munki."""

    fixtures = ['machine_group_fixture.json', 'business_unit_fixture.json', 'machine_fixture.json']

    def setUp(self):
        settings.BASIC_AUTH = False
        self.client = Client()
        self.content_type = 'application/json'
        self.url = '/checkin/'
        # Avoid sending analytics to the project while testing!
        server.utils.set_setting('send_data', False)

    def test_managed_item_created(self):
        """Test that managed items get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        manifest = 'the_firm'
        munki_version = '1000.0.0'
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key},
            'munki': {'manifest': manifest, 'munki_version': munki_version}})
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        self.assertEqual(machine.manifest, manifest)
        self.assertEqual(machine.munki_version, munki_version)

    def test_pending_apple_item_created(self):
        """Test that pending apple updates get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key},
            'munki': {
                'update_history': [
                    {'update_type': 'apple',
                     'name': 'macOS 10.99.1 Heavy Metal Update',
                     'version': '1.0.0',
                     'date': '2050-01-30T13:00:00Z',
                     'status': 'pending'}]}})
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        self.assertTrue(PendingAppleUpdate.objects.exists())

    def test_update_history_creation(self):
        """Test that update histories get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key},
            'munki': {
                'update_history': [
                    {'update_type': 'apple',
                     'name': 'macOS 10.99.1 Heavy Metal Update',
                     'version': '1.0.0',
                     'date': '2050-01-30T13:00:00Z',
                     'status': 'pending'}]}})
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        self.assertTrue(UpdateHistory.objects.exists())

    def test_update_history_item_creation(self):
        """Test that update history items get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key},
            'munki': {
                'update_history': [
                    {'update_type': 'apple',
                     'name': 'macOS 10.99.1 Heavy Metal Update',
                     'version': '1.0.0',
                     'date': '2050-01-30T13:00:00Z',
                     'status': 'pending'}]}})
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        self.assertTrue(UpdateHistoryItem.objects.exists())

    def test_update_history_item_skipped(self):
        """Test that update history items are skipped when duplicate."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        update_type = 'third_party'
        name = 'Dwarf Fortress'
        version = '1.5'
        status = 'pending'
        recorded = '2050-01-30T13:00:00Z'

        update_history = UpdateHistory.objects.create(
            machine=machine, update_type=update_type, name=name, version=version)
        UpdateHistoryItem.objects.create(
            update_history=update_history, status=status, recorded=recorded)

        data = json.dumps({
            'machine': {'serial': machine.serial},
            'sal': {'key': machine.machine_group.key},
            'munki': {
                'update_history': [
                    {'update_type': update_type,
                     'name': name,
                     'version': version,
                     'date': recorded,
                     'status': status}]}})
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        self.assertTrue(UpdateHistoryItem.objects.count() == 1)


class CheckinHelperTest(TestCase):
    """Tests for helper functions that support the checkin view."""

    fixtures = ['machine_group_fixture.json', 'business_unit_fixture.json', 'machine_fixture.json']

    def setUp(self):
        self.report = {'test': 'I heard you were dead'}

    def test_vmware_serial(self):
        """Ensure serial translation for crazy VMWare serials works."""
        machine = non_ui_views.process_checkin_serial('+/c0deadbEEF')
        self.assertEqual(machine.serial, 'C0DEADBEEF')

    def test_machine_from_valid_serial(self):
        """Ensure we can get an existing Machine object."""
        machine = non_ui_views.process_checkin_serial('C0DEADBEEF')
        self.assertEqual(machine.pk, 1)

    @patch('server.non_ui_views.settings.ADD_NEW_MACHINES', True)
    def test_add_new_machine(self):
        """Ensure we can add a new machine with ADD_NEW_MACHINES=True"""
        machine = non_ui_views.process_checkin_serial('NotInDB')
        self.assertEqual(machine.pk, None)

    @patch('server.non_ui_views.settings.ADD_NEW_MACHINES', False)
    def test_no_add_new_machine(self):
        """Ensure 404 is raised when no ADD_NEW_MACHINES."""
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
