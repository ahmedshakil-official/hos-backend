import json
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase

from .. tests import UnitFactory
from ..models import Unit

class UnitDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(UnitDetailsAPITest,self).setUp()

        # set a product group
        self.unit = UnitFactory(organization=self.admin_user.organization)
        # set the url
        self.url = reverse('pharmacy.unit-details',
                           args=[self.unit.alias])

    def test_unit_details_get(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================
        # self.admin_user.organization = self.user.organization
        # self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # Check if is the same data
        self.assertEqual(request.data['id'], self.unit.id)
        self.assertEqual(request.data['name'], self.unit.name)
        self.assertEqual(request.data['alias'], str(self.unit.alias))

        # admin user logout
        self.client.logout()

    def test_unit_details_put(self):
        data = {
            'name': self.fake.first_name(),
            'description': self.fake.text()
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.put(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.put(self.url, data)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.put(self.url, data=json.dumps(dict(data)), content_type='application/json')
        self.assertSuccess(request)

        # Check if it is the same data
        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['description'], data['description'])

        # admin user logout
        self.client.logout()


    def test_product_group_details_delete(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.delete(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.delete(self.url)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        self.assertEqual(Unit.objects.count(), 1)
        request = self.client.delete(self.url)
        self.assertDeleted(request)

        # admin user logout
        self.client.logout()
