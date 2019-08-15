"""Tests for the Inventory App"""


from django.test import TestCase

from server.models import BusinessUnit, MachineGroup, Machine, User, UserProfile


class AccessTestCase(TestCase):
    """Ensure access decorators are limiting access correctly"""
    fixtures = [
        'machine_fixtures.json', 'business_unit_fixtures.json', 'machine_group_fixtures.json']

    def setUp(self):
        self.test_user = User.objects.create(username='test')

    def test_login_redirect(self):
        url = '/inventory/all/0/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/login?next={}'.format(url))

    def test_no_access(self):
        self.client.force_login(self.test_user)
        response = self.client.get('/inventory/all/0/')
        self.assertEqual(response.status_code, 403)
        response = self.client.get('/inventory/business_unit/1/')
        self.assertEqual(response.status_code, 403)
        response = self.client.get('/inventory/machine_group/1/')
        self.assertEqual(response.status_code, 403)
        response = self.client.get('/inventory/machine/1/')
        self.assertEqual(response.status_code, 403)

    def test_access_403(self):
        self.client.force_login(self.test_user)

        # User should not have access to anything yet (404)
        response = self.client.get('/inventory/machine/3/')
        self.assertEqual(response.status_code, 404)

        # Add GA privileges to user and try again
        # Expect 404 since it doesn't exist!
        profile = UserProfile.objects.get(pk=self.test_user.userprofile.id)
        profile.level = 'GA'
        profile.save()
        response = self.client.get('/inventory/machine/3/')
        self.assertEqual(response.status_code, 404)

    def test_access(self):
        self.client.force_login(self.test_user)

        business_unit = BusinessUnit.objects.get(pk=1)
        business_unit.users.add(self.test_user)

        response = self.client.get('/inventory/business_unit/1/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/inventory/machine_group/1/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/inventory/machine/1/')
        self.assertEqual(response.status_code, 200)


class ApplicationDetailTestCase(TestCase):
    """Exercise the application detail view"""
    fixtures = ['application_fixture.json', 'machine_fixtures.json',
                'business_unit_fixtures.json', 'machine_group_fixtures.json']

    def setUp(self):
        self.test_user = User.objects.create(username='test')
        business_unit = BusinessUnit.objects.get(pk=1)
        business_unit.users.add(self.test_user)
        self.client.force_login(self.test_user)

    def test_application_detail_ga(self):
        business_unit = BusinessUnit.objects.get(pk=2)
        business_unit.users.add(self.test_user)
        response = self.client.get('/inventory/application/all/0/1/')
        self.assertEqual(response.status_code, 200)

    def test_application_detail_bu(self):
        response = self.client.get('/inventory/application/business_unit/1/1/')
        self.assertEqual(response.status_code, 200)

    def test_application_detail_mg(self):
        response = self.client.get('/inventory/application/machine_group/1/1/')
        self.assertEqual(response.status_code, 200)

    def test_application_detail_machine(self):
        self.client.force_login(self.test_user)
        response = self.client.get('/inventory/application/machine/1/1/')
        self.assertEqual(response.status_code, 200)

    def test_application_detail_content(self):
        self.client.force_login(self.test_user)
        response = self.client.get('/inventory/application/machine/1/1/')
        self.assertEqual(response.context['install_count'], 1)
        self.assertEqual(len(response.context['paths']), 1)
        self.assertIn('count', response.context['paths'][0])
        self.assertIn('path', response.context['paths'][0])
        self.assertEqual(len(response.context['versions']), 1)
        self.assertIn('count', response.context['versions'][0])
        self.assertIn('version', response.context['versions'][0])
        self.assertEqual(response.context['application'].bundlename, 'TacoFortress')
