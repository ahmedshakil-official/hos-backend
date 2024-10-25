from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase

from ..tests import StorePointFactory


class StockListBatchwiseAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(StockListBatchwiseAPITest, self).setUp()

        self.store = StorePointFactory(organization=self.admin_user.organization)

        self.url = reverse(
            'pharmacy.stock-list-batchwise', args=[self.store.id]
        )

    def test_stock_list_get(self):
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
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        # calling the api
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # admin user logout
        self.client.logout()
