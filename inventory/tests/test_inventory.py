"""Tests for the Inventory App"""


from django.test import TestCase

from server.models import BusinessUnit, MachineGroup, Machine, User, UserProfile


class AccessTestCase(TestCase):
    """Ensure access decorators are limiting access correctly"""

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

    def test_access_404(self):
        self.client.force_login(self.test_user)

        # User should not have access to anything yet (403)
        response = self.client.get('/inventory/machine/1/')
        self.assertEqual(response.status_code, 403)

        # Add GA privileges to user and try again
        # Expect 404 since it doesn't exist!
        profile = UserProfile.objects.get(pk=self.test_user.userprofile.id)
        profile.level = 'GA'
        profile.save()
        response = self.client.get('/inventory/machine/1/')
        self.assertEqual(response.status_code, 404)

    def test_access(self):
        self.client.force_login(self.test_user)

        business_unit = BusinessUnit.objects.create(name='TestBU')
        machine_group = MachineGroup.objects.create(name='TestMG', business_unit=business_unit)
        machine = Machine.objects.create(serial='C0DEADBEEF', machine_group=machine_group)

        business_unit.users.add(self.test_user)
        response = self.client.get('/inventory/business_unit/1/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/inventory/machine_group/1/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/inventory/machine/1/')
        self.assertEqual(response.status_code, 200)
