import json
from django.urls import reverse
from faker import Faker

from common.test_case import OmisTestCase
from core.tests import DiscountGroupFactory

from ..models import DiscountGroup


class DiscountGroupDetailsAPITest(OmisTestCase):
    url = None
    fake = Faker()

    def setUp(self):
        super(DiscountGroupDetailsAPITest, self).setUp()

        # set a discount group
        self.discount_group = DiscountGroupFactory(organization=self.admin_user.organization)

        # set the url
        self.url = reverse('discount-group-details', args=[self.discount_group.alias])

    def test_discount_group_details_get(self):

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
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # admin user logout
        self.client.logout()

    def test_discount_group_details_put(self):
        data = {
            'name': self.fake.first_name(),
            'description': self.fake.text(),
            'organization': self.admin_user.organization.id
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.put(self.url)
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
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.put(self.url, data=json.dumps(
            dict(data)), content_type='application/json')
        self.assertSuccess(request)

        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['description'], data['description'])
        self.assertEqual(request.data['organization'], data['organization'])


        # admin user logout
        self.client.logout()

    def test_discount_group_details_delete(self):

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.put(self.url)
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
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.delete(self.url)
        self.assertDeleted(request)

        # admin user logout
        self.client.logout()
