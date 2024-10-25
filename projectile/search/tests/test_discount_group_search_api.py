from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status
from core.tests import DiscountGroupFactory

from faker import Faker


class DiscountGroupSearchAPITest(OmisTestCase):
    url = reverse('discount-group-search')
    fake = Faker()

    def test_discount_group_search_get(self):
        discount_group = DiscountGroupFactory(
            organization=self.admin_user.organization,
            status=Status.ACTIVE,
            name=self.fake.first_name()
        )

        # search data
        data1 = {
            'keyword': discount_group.name
        }

        data2 = {
            'keyword': self.fake.first_name()
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        self.assertEqual(
            request.data['results'][0]['name'], discount_group.name
        )

        # check with another keywod
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 0)

        # logout
        self.client.logout()
