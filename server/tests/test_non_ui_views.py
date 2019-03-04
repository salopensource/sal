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
    MachineGroup, Machine, ManagementSource, ManagedItem, Fact, HistoricalFact, Message)


class CheckinDataTest(TestCase):
    """Functional tests for client checkins."""

    fixtures = [
        'machine_group_fixtures.json', 'business_unit_fixtures.json', 'machine_fixtures.json']

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
        self.assertEqual(response.content, b'Checkin JSON is missing required key "Machine"!')

    def test_checkin_data_missing_required_serial_key(self):
        """Ensure that checkins with no machine dict get a 400 response."""
        response = self.client.post(
            self.url, data=json.dumps({'Machine': {}}), content_type=self.content_type)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.content, b'Checkin JSON is missing required "Machine" key "serial"!')

    def test_checkin_data_missing_required_machine_group_key(self):
        """Ensure that checkins with no machine_gruop key get a 400 response."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': 'Not a key'}}})
        response = self.client.post(self.url, data=data, content_type=self.content_type)
        self.assertEqual(response.status_code, 404)

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
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}}})
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
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}}})
        self.client.post(self.url, data=data, content_type=self.content_type)
        machine.refresh_from_db()
        self.assertFalse(machine.deployed)

    def test_new_machine_on_checkin(self):
        """Test that a machine gets created when it doesn't already exist."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        test_serial = 'New machine'.upper()
        settings.ADD_NEW_MACHINES = True
        data = json.dumps({
            'Machine': {'extra_data': {'serial': test_serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}}})
        self.client.post(self.url, data=data, content_type=self.content_type)
        self.assertTrue(Machine.objects.get(serial=test_serial))

    def test_no_new_machine_on_checkin(self):
        """Test that a machine doesn't get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        test_serial = 'New machine'.upper()
        settings.ADD_NEW_MACHINES = False
        data = json.dumps({
            'Machine': {'extra_data': {'serial': test_serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}}})
        self.client.post(self.url, data=data, content_type=self.content_type)
        machine.refresh_from_db()
        self.assertRaises(Machine.DoesNotExist, Machine.objects.get, serial=test_serial)

    def test_minimal_data(self):
        """Test checkin can complete with bare minimum data."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}}})
        response = self.client.post(self.url, data, content_type=self.content_type)
        self.assertEqual(response.status_code, 200)

    def test_management_source_creation(self):
        """Test checkin creates management sources."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}},
            'Munki': {}})
        self.client.post(self.url, data, content_type=self.content_type)
        self.assertTrue(ManagementSource.objects.filter(name='Munki').exists())


class BrokenClientTest(TestCase):
    """Functional tests for broken client checkins."""

    fixtures = [
        'machine_group_fixtures.json', 'business_unit_fixtures.json', 'machine_fixtures.json']

    def setUp(self):
        settings.BASIC_AUTH = False
        self.client = Client()
        self.url = '/report_broken_client/'


    def test_broken_client_checkin(self):
        """Test that a machine's broken bool is updated on checkin."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = {
            'serial': machine.serial,
            'key': machine.machine_group.key,
            'broken_client': True}
        response = self.client.post(self.url, data=data)
        machine.refresh_from_db()
        self.assertTrue(machine.broken_client)
        self.assertEqual(
            response.content, b'Broken Client report submmitted for %s' % machine.serial.encode())


class CheckinFactTest(TestCase):
    """Functional tests for client checkins for Fact/HistoricalFact."""

    fixtures = [
        'machine_group_fixtures.json', 'business_unit_fixtures.json', 'machine_fixtures.json',
        'fact_fixtures.json']

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
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}}})
        self.client.post(self.url, data, content_type=self.content_type)
        self.assertEqual(Fact.objects.count(), 0)

    def test_facts_created(self):
        """Test that facts get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}},
            'Munki': {'facts': {'test_user': 'Snake Plisskin'}}
        })
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        fact = machine.facts.get(fact_name='test_user')
        self.assertEqual(fact.fact_name, 'test_user')
        self.assertEqual(fact.fact_data, 'Snake Plisskin')
        self.assertEqual(fact.management_source.name, 'Munki')

    @patch('server.non_ui_views.HISTORICAL_FACTS', ['test_user'])
    def test_historical_facts_created(self):
        """Test historical facts get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}},
            'Munki': {'facts': {'test_user': 'Snake Plisskin'}}
        })
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        fact = machine.facts.get(fact_name='test_user')
        historical_fact = machine.historical_facts.get(fact_name='test_user')
        self.assertEqual(fact.fact_name, 'test_user')
        self.assertEqual(fact.fact_data, 'Snake Plisskin')
        self.assertEqual(fact.management_source.name, 'Munki')
        self.assertEqual(historical_fact.fact_name, 'test_user')
        self.assertEqual(historical_fact.fact_data, 'Snake Plisskin')
        self.assertEqual(historical_fact.management_source.name, 'Munki')

    @patch('server.non_ui_views.IGNORE_PREFIXES', ['ignore'])
    def test_ignore_facts_setting_works(self):
        """Test the ignore prefixes setting for facts works."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}},
            'Munki': {'facts': {'test_user': 'Snake Plisskin', 'ignore_this': 'Yep'}}
        })
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        self.assertRaises(Fact.DoesNotExist, machine.facts.get, fact_name='ignore_this')


class CheckinMessageTest(TestCase):
    """Functional tests for client checkins for Message."""

    fixtures = [
        'machine_group_fixtures.json', 'business_unit_fixtures.json', 'machine_fixtures.json',
        'message_fixtures.json']

    def setUp(self):
        settings.BASIC_AUTH = False
        self.client = Client()
        self.content_type = 'application/json'
        self.url = '/checkin/'
        # Avoid sending analytics to the project while testing!
        server.utils.set_setting('send_data', False)

    def test_messages_cleanup(self):
        """Test that all of a machine's messages get dropped."""
        # TODO: There are none at this point, so this test is kind of lame
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}}})
        self.client.post(self.url, data, content_type=self.content_type)
        self.assertEqual(Message.objects.count(), 0)

    def test_messages_created(self):
        """Test that messages get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        text = 'I heard you were dead...'
        data = json.dumps({
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}},
            'Munki': {'messages': [{'text': text, 'message_type': 'WARNING'}]}
        })
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        message = machine.messages.get(text=text)
        self.assertEqual(message.text, text)
        self.assertEqual(message.message_type, 'WARNING')


class CheckinManagedItemTest(TestCase):
    """Functional tests for client checkins for ManagedItem."""

    fixtures = [
        'machine_group_fixtures.json', 'business_unit_fixtures.json', 'machine_fixtures.json']

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
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}}})
        self.client.post(self.url, data, content_type=self.content_type)
        self.assertEqual(ManagedItem.objects.count(), 0)

    def test_managed_item_created(self):
        """Test that managed items get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        data = json.dumps({
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}},
            'Munki': {'managed_items': {
                'Dwarf Fortress': {}}}})
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        managed_item = machine.manageditem_set.get(name='Dwarf Fortress')
        self.assertEqual(managed_item.name, 'Dwarf Fortress')
        self.assertEqual(managed_item.management_source.name, 'Munki')

    @patch('django.utils.timezone.now')
    def test_managed_item_created_with_defaults(self, mock_now):
        """Test that managed items get created."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        mock_now.return_value = now()
        data = json.dumps({
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}},
            'Munki': {'managed_items': {
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
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}},
            'Munki': {'managed_items': {
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

    fixtures = [
        'machine_group_fixtures.json', 'business_unit_fixtures.json', 'machine_fixtures.json']

    def setUp(self):
        settings.BASIC_AUTH = False
        self.client = Client()
        self.content_type = 'application/json'
        self.url = '/checkin/'
        # Avoid sending analytics to the project while testing!
        server.utils.set_setting('send_data', False)

    def test_munki_fields_set(self):
        """Test that Munki machine fields get set."""
        machine = Machine.objects.get(serial='C0DEADBEEF')
        manifest = 'the_firm'
        munki_version = '1000.0.0'
        data = json.dumps({
            'Machine': {'extra_data': {'serial': machine.serial}},
            'Sal': {'extra_data': {'key': machine.machine_group.key}},
            'Munki': {'extra_data': {'manifest': manifest, 'munki_version': munki_version}}})
        self.client.post(self.url, data, content_type=self.content_type)
        machine.refresh_from_db()
        self.assertEqual(machine.manifest, manifest)
        self.assertEqual(machine.munki_version, munki_version)


class CheckinManagedItemHistoryTest(TestCase):
    """Functional tests for client checkins for ManagedItemHistory."""

    fixtures = [
        'machine_group_fixtures.json', 'business_unit_fixtures.json', 'machine_fixtures.json']

    def setUp(self):
        settings.BASIC_AUTH = False
        self.client = Client()
        self.content_type = 'application/json'
        self.url = '/checkin/'
        # Avoid sending analytics to the project while testing!
        server.utils.set_setting('send_data', False)

    # TODO: Write!
    # def test_pending_managed_item_created(self):
    #     """Test that pending managed updates get created."""
    #     machine = Machine.objects.get(serial='C0DEADBEEF')
    #     data = json.dumps({
    #         'Machine': {'serial': machine.serial},
    #         'Sal': {'key': machine.machine_group.key},
    #         'Munki': {
    #             'managed_items': {
    #                 'macOS 10.99.1 Heavy Metal Update': {
    #                     'date_managed': '2050-01-30T13:00:00Z', 'status': 'PENDING'}
    #             }}})
    #     self.client.post(self.url, data, content_type=self.content_type)
    #     machine.refresh_from_db()
    #     self.assertTrue(.objects.exists())

    # def test_update_history_creation(self):
    #     """Test that update histories get created."""
    #     machine = Machine.objects.get(serial='C0DEADBEEF')
    #     data = json.dumps({
    #         'Machine': {'serial': machine.serial},
    #         'Sal': {'key': machine.machine_group.key},
    #         'Munki': {
    #             'update_history': [
    #                 {'update_type': 'apple',
    #                  'name': 'macOS 10.99.1 Heavy Metal Update',
    #                  'version': '1.0.0',
    #                  'date': '2050-01-30T13:00:00Z',
    #                  'status': 'pending'}]}})
    #     self.client.post(self.url, data, content_type=self.content_type)
    #     machine.refresh_from_db()
    #     self.assertTrue(UpdateHistory.objects.exists())

    # def test_update_history_item_creation(self):
    #     """Test that update history items get created."""
    #     machine = Machine.objects.get(serial='C0DEADBEEF')
    #     data = json.dumps({
    #         'Machine': {'serial': machine.serial},
    #         'Sal': {'key': machine.machine_group.key},
    #         'Munki': {
    #             'update_history': [
    #                 {'update_type': 'apple',
    #                  'name': 'macOS 10.99.1 Heavy Metal Update',
    #                  'version': '1.0.0',
    #                  'date': '2050-01-30T13:00:00Z',
    #                  'status': 'pending'}]}})
    #     self.client.post(self.url, data, content_type=self.content_type)
    #     machine.refresh_from_db()
    #     self.assertTrue(UpdateHistoryItem.objects.exists())

    # def test_update_history_item_skipped(self):
    #     """Test that update history items are skipped when duplicate."""
    #     machine = Machine.objects.get(serial='C0DEADBEEF')
    #     update_type = 'third_party'
    #     name = 'Dwarf Fortress'
    #     version = '1.5'
    #     status = 'pending'
    #     recorded = '2050-01-30T13:00:00Z'

    #     update_history = UpdateHistory.objects.create(
    #         machine=machine, update_type=update_type, name=name, version=version)
    #     UpdateHistoryItem.objects.create(
    #         update_history=update_history, status=status, recorded=recorded)

    #     data = json.dumps({
    #         'Machine': {'serial': machine.serial},
    #         'Sal': {'key': machine.machine_group.key},
    #         'Munki': {
    #             'update_history': [
    #                 {'update_type': update_type,
    #                  'name': name,
    #                  'version': version,
    #                  'date': recorded,
    #                  'status': status}]}})
    #     self.client.post(self.url, data, content_type=self.content_type)
    #     machine.refresh_from_db()
    #     self.assertTrue(UpdateHistoryItem.objects.count() == 1)


class CheckinHelperTest(TestCase):
    """Tests for helper functions that support the checkin view."""

    fixtures = [
        'machine_group_fixtures.json', 'business_unit_fixtures.json', 'machine_fixtures.json']

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
