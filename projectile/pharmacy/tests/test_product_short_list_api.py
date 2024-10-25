from django.urls import reverse
import random
from faker import Faker
from common.test_case import OmisTestCase
from ..tests import StorePointFactory, StockFactory


class ProductShortListAPITest(OmisTestCase):
    url = reverse('pharmacy.product-short-report')
    fake = Faker()

    def test_product_short_list_get(self):
        store_point = StorePointFactory(
            organization=self.admin_user.organization
        )
        stock_product = StockFactory.create_batch(
            10,
            organization=self.admin_user.organization,
            minimum_stock=random.randint(15, 20),
            stock=random.randint(10, 20),
            store_point=store_point
        )
        short_list = [
            stock for stock in stock_product if stock.stock <= stock.minimum_stock
            ]
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

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)
        self.assertEqual(request.data['count'], len(short_list))

        # admin user logout
        self.client.logout()
