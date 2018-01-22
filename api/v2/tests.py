from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from server.models import *


class MachinesTest(APITestCase):

    def setUp(self):
        api_key = ApiKey.objects.create()
        self.headers = {'HTTP_PRIVATEKEY': api_key.private_key, 'HTTP_PUBLICKEY': api_key.public_key}
        bu = BusinessUnit.objects.create(name='test')
        mg = MachineGroup.objects.create(name='test', business_unit=bu)
        Machine.objects.create(serial='C0DEADBEEF', machine_group=mg)

    def test_access(self):
        response = self.client.get(reverse('machine-list'))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['content-type'], 'application/json')

    def test_get_returns_json_200(self):
        response = self.client.get(reverse('machine-list'), {}, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')

    def test_get_by_serial(self):
        response = self.client.get(reverse('machine-detail', args=('C0DEADBEEF',)), {}, **self.headers)
        self.assertEqual(response.status_code, 200)

    def test_get_by_id_returns_404(self):
        response = self.client.get(reverse('machine-detail', args=(1,)), {}, **self.headers)
        self.assertEqual(response.status_code, 404)

    def test_get_with_full(self):
        response = self.client.get(reverse('machine-detail', args=('C0DEADBEEF',)), {}, **self.headers)
        full_response = self.client.get(reverse('machine-detail', args=('C0DEADBEEF',)), {'full': None}, **self.headers)
        short = response.json()
        full = full_response.json()
        self.assertNotEqual(len(short), len(full))
        self.assertTrue('activity' in full)
        self.assertFalse('activity' in short)

    def test_include_fields(self):
        response = self.client.get(reverse('machine-detail', args=('C0DEADBEEF',)), {'fields': 'activity', 'fields!': 'hostname' }, **self.headers)
        self.assertIn('activity', response.data)
        self.assertNotIn('hostname', response.data)

    def test_list_include_fields(self):
        response = self.client.get(reverse('machine-list'), {'fields': 'activity', 'fields!': 'hostname' }, **self.headers)
        record = response.data['results'][0]
        self.assertIn('activity', record)
        self.assertNotIn('hostname', record)
