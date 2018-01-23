"""Tools used in testing the Sal API app."""


import contextlib
import cStringIO
import sys

from django.urls import reverse

from rest_framework.test import APITestCase

from server.models import (ApiKey, BusinessUnit, MachineGroup, Machine)


# Get rid of pylint complaining about Django ORM stuff
# pylint: disable=no-member


@contextlib.contextmanager
def no_stdout():
    """Method decorator to prevent stdout from mucking up test output"""
    saved_stdout = sys.stdout
    sys.stdout = cStringIO.StringIO()
    try:
        yield
    except Exception:
        saved_output = sys.stdout
        sys.stdout = saved_stdout
        print saved_output.getvalue()
        raise
    sys.stdout = saved_stdout


class SalAPITestCase(APITestCase):
    """Overriden DRF TestCase to simplify data setup and authenticated
    request generation.
    """
    setup_data = []

    def setUp(self):
        # Set up an APIKey for authenticated tests to use.
        api_key = ApiKey.objects.create()
        self.headers = {
            'HTTP_PRIVATEKEY': api_key.private_key,
            'HTTP_PUBLICKEY': api_key.public_key}

        for data_method_name in self.setup_data:
            data_method = getattr(self, data_method_name)
            data_method()

    # pylint: disable=no-self-use
    def create_machine_data(self):
        """Created all data needed for machine testing."""
        business_unit = BusinessUnit.objects.create(name='test')
        machine_group = MachineGroup.objects.create(
            name='test', business_unit=business_unit)
        Machine.objects.create(
            serial='C0DEADBEEF', machine_group=machine_group)
        Machine.objects.create(
            serial='C1DEADBEEF', machine_group=machine_group)

    def authed_get(self, name, args=None, params=None):
        """Perform an authenticated get request to API."""
        if not params:
            params = {}
        url = reverse(name, args=args) if args else reverse(name)

        return self.client.get(url, params, **self.headers)
    def authed_options(self, name, args=None, params=None):
        """Perform an authenticated get request to API."""
        if not params:
            params = {}
        url = reverse(name, args=args) if args else reverse(name)

        return self.client.options(url, params, **self.headers)
