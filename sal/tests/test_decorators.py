"""General functional tests for the server app."""


from django.http.response import Http404, HttpResponseServerError
from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.urls import reverse

from sal.decorators import *
from sal.decorators import get_business_unit_by as func_get_business_unit
from server.models import *


SUCCESS = 'Nice work, amigo.'


class AccessFunctionTest(TestCase):
    fixtures = ['user_fixture.json', 'business_unit_fixtures.json', 'machine_group_fixtures.json',
                'machine_fixtures.json']

    def setUp(self):
        self.user = User.objects.get(pk=2)
        self.ga_user = User.objects.get(pk=1)
        user_profile = self.ga_user.userprofile
        user_profile.level = 'GA'
        user_profile.save()
        self.business_unit = BusinessUnit.objects.get(pk=1)
        self.business_unit2 = BusinessUnit.objects.get(pk=2)

    def test_no_membership_has_access(self):
        self.assertFalse(has_access(self.user, self.business_unit))

    def test_member_has_access(self):
        self.business_unit.users.add(self.user)
        self.assertTrue(has_access(self.user, self.business_unit))

    def test_ga_has_access(self):
        self.assertTrue(has_access(self.ga_user, self.business_unit))

    def test_all_bu_has_access(self):
        """Test has_access with user who has all BU membership.

        If user is member of all bus, ensure access to 'all' dashboards
        """
        # Currently, "None" business units are only used by the
        # inventory app.
        self.assertFalse(has_access(self.user, None))
        self.business_unit.users.add(self.user)
        self.business_unit2.users.add(self.user)
        self.assertTrue(has_access(self.user, None))

    def test_get_business_unit(self):
        self.assertEqual(
            (self.business_unit, self.business_unit), func_get_business_unit(BusinessUnit, bu_id=1))

    def test_get_business_unit_from_mg(self):
        machine_group = MachineGroup.objects.get(pk=1)
        self.assertEqual(
            (machine_group, self.business_unit), func_get_business_unit(MachineGroup, mg_id=1))

    def test_get_business_unit_from_machine(self):
        machine = Machine.objects.get(pk=1)
        self.assertEqual(
            (machine, self.business_unit), func_get_business_unit(Machine, machine_id=1))
        self.assertEqual(
            (machine, self.business_unit), func_get_business_unit(Machine, machine_id='C0DEADBEEF'))

    def test_get_business_unit_errors(self):
        self.assertRaises(
            Http404, func_get_business_unit, MachineGroup, mg_id=500)
        self.assertRaises(
            Http404, func_get_business_unit, Machine, machine_id='DOES_NOT_EXIST')
        self.assertRaises(
            ValueError, func_get_business_unit, Machine, not_the_kwarg_you_are_looking_for=0)

    def test_is_global_admin(self):
        self.assertTrue(is_global_admin(self.ga_user))
        self.assertFalse(is_global_admin(self.user))


class FunctionDecoratorsTest(TestCase):
    """Test the view function access decorators."""
    fixtures = ['user_fixture.json', 'business_unit_fixtures.json']

    def setUp(self):
        self.factory = RequestFactory()
        self.normal_user = User.objects.get(pk=2)
        self.staff_user = User.objects.get(pk=1)

        @access_required(BusinessUnit)
        def test_view(request, **kwargs):
            return SUCCESS

        self.test_view = test_view

    def test_access_required_for_nonmembers(self):
        request = self.factory.get('/test/')
        # functools.wraps has a conniption because this is missing.
        request.__name__ = 'Test'
        request.user = self.normal_user
        self.assertRaises(PermissionDenied, self.test_view, request, bu_id=2)

    def test_access_required_with_member(self):
        request = self.factory.get('/test/')
        # functools.wraps has a conniption because this is missing.
        request.__name__ = 'Test'
        BusinessUnit.objects.get(pk=1).users.add(self.normal_user)
        request.user = self.normal_user
        response = self.test_view(request, bu_id=1)
        self.assertEqual(response, SUCCESS)

    def test_access_required_with_ga(self):
        request = self.factory.get('/test/')
        # functools.wraps has a conniption because this is missing.
        request.__name__ = 'Test'
        user_profile = self.staff_user.userprofile
        user_profile.level = 'GA'
        user_profile.save()
        request.user = self.staff_user
        response = self.test_view(request, bu_id=1)
        self.assertEqual(response, SUCCESS)

    def test_key_auth_required(self):

        @key_auth_required
        def test_view(request, *args, **kwargs):
            return SUCCESS

        # TODO: Needs to be written to test for:
        # - BASIC_AUTH not set (use_auth defaults to True)
        # - BASIC_AUTH = false
        # - BASIC_AUTH = True
        pass

    def test_required_level(self):

        @required_level(ProfileLevel.global_admin, ProfileLevel.read_write)
        def test_view(request, *args, **kwargs):
            return SUCCESS

        request = self.factory.get('/test/')
        request.user = self.normal_user
        response = test_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

        # Elevate user to RW status.
        request = self.factory.get('/test/')
        user_profile = self.normal_user.userprofile
        user_profile.level = 'RW'
        user_profile.save()
        request.user = self.normal_user
        response = test_view(request)
        self.assertEqual(response, SUCCESS)

        # Elevate staff user to GA status.
        request = self.factory.get('/test/')
        user_profile = self.staff_user.userprofile
        user_profile.level = 'GA'
        user_profile.save()
        request.user = self.staff_user
        response = test_view(request)
        self.assertEqual(response, SUCCESS)

    def test_staff_required(self):

        @staff_required
        def test_view(request, *args, **kwargs):
            return SUCCESS

        request = self.factory.get('/test/')
        request.user = self.normal_user
        response = test_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

        request = self.factory.get('/test/')
        request.user = self.staff_user
        response = test_view(request)
        self.assertEqual(response, SUCCESS)
