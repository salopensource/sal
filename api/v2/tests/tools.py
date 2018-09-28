"""Tools used in testing the Sal API app."""


import contextlib
import io
import sys

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from server.models import (ApiKey, BusinessUnit, MachineGroup, Machine)


# Get rid of pylint complaining about Django ORM stuff
# pylint: disable=no-member


@contextlib.contextmanager
def no_stdout():
    """Method decorator to prevent stdout from mucking up test output"""
    saved_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield
    except Exception:
        saved_output = sys.stdout
        sys.stdout = saved_stdout
        print(saved_output.getvalue())
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
        machine_group = self.create_machine_group_data()
        Machine.objects.create(
            serial='C0DEADBEEF', machine_group=machine_group)
        Machine.objects.create(
            serial='C1DEADBEEF', machine_group=machine_group)

    # pylint: disable=no-self-use
    def create_business_unit_data(self):
        """Set up business unit data."""
        return BusinessUnit.objects.create(name='test')

    # pylint: disable=no-self-use
    def create_machine_group_data(self):
        """Set up machine group and dependent data."""
        business_unit = self.create_business_unit_data()
        return MachineGroup.objects.create(
            name='test', business_unit=business_unit)

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


class TestGeneratorMeta(type):
    """Automatically generate basic tests for 'boring' endpoints.

    By replacing a UnitTest subclass' metaclass with this, and by adding
    a `tests` class property, you can automatically generate access,
    listing, and detail tests (that basically just ensure they return
    200 at this time).

    `tests` should be an iterable of route names (lowercase,
    underscores stripped).
    """

    def __new__(mcs, name, bases, attrs):
        """Override new to create our test methods with correct names"""

        for test_name in attrs['tests']:
            access_method, list_method, detail_method = mcs.generate_tests(
                test_name)
            attrs['test_{}_access'.format(test_name)] = access_method
            attrs['test_{}_list'.format(test_name)] = list_method
            attrs['test_{}_detail'.format(test_name)] = detail_method

        return super(TestGeneratorMeta, mcs).__new__(mcs, name, bases, attrs)

    @classmethod
    def generate_tests(mcs, route_name):
        """Generate the tests to attach to the new class."""

        def access_method(self):
            """Test that unauthenticated access is denied."""
            response = self.client.get(reverse('{}-list'.format(route_name)))
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        def list_method(self):
            """Test that listing operations work"""
            response = self.authed_get('{}-list'.format(route_name))
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        def detail_method(self):
            """Test that detail operations work"""
            response = self.authed_get(
                '{}-detail'.format(route_name), args=(1,))
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        return (access_method, list_method, detail_method)
