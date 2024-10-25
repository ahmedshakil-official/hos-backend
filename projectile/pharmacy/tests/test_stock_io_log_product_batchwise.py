import datetime, random
from faker import Faker

from django.urls import reverse
from common.test_case import OmisTestCase
from ..tests import StockIOLogFactory, StorePointFactory, StockFactory


class StockProductBatchListAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(StockProductBatchListAPITest, self).setUp()

        self.store = StorePointFactory(organization=self.admin_user.organization)
        self.stock_io_log = StockIOLogFactory(organization=self.admin_user.organization)
        self.url = reverse('pharmacy.product-batchwise',
                           args=[self.stock_io_log.stock.product.id])

    def test_stock_list_product_batch_wise_get(self):
        random_counter = random.randint(5, 6)
        stock_1 = StockIOLogFactory.create_batch(random_counter - 1, organization=self.admin_user.organization,
                                                 stock=StockFactory(organization=self.admin_user.organization,
                                                                    product=self.stock_io_log.stock.product,
                                                                    store_point=self.store))

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
        length = len(request.data)
        self.assertEqual(length, random_counter)

        self.client.logout()
