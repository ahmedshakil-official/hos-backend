import random
import string
import datetime
from faker import Faker

from django.urls import reverse
from common.test_case import OmisTestCase
from ..tests import StockIOLogFactory, StorePointFactory, StockFactory
from ..enums import StockIOType


def random_batch(batch_length=5):
    """Generate a random Batch of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(batch_length))


class StockListBatchStoreDateWiseAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(StockListBatchStoreDateWiseAPITest, self).setUp()

        self.store = StorePointFactory(organization=self.admin_user.organization)
        self.stock_io_log = StockIOLogFactory(organization=self.admin_user.organization)
        self.date_to_find = datetime.date.today()
        date = str(self.date_to_find)
        dates = date.split("-")

        self.url = reverse(
            'pharmacy.stock-list-product-batchwise-date',
            args=[self.store.id, self.stock_io_log.stock.product.id, dates[0], dates[1], dates[2]]
        )

    def test_stock_list_get(self):
        random_counter = random.randint(5, 6)
        quantity = random.randint(4, 6)
        StorePointFactory(organization=self.admin_user.organization)
        stock_1 = []
        for _ in range(random_counter):
            batch = random_batch()
            stock = StockIOLogFactory(
                organization=self.admin_user.organization,
                expire_date=str(self.date_to_find), batch=batch,
                date=str(self.date_to_find), quantity=quantity, purchase=None,
                stock=StockFactory(
                    organization=self.admin_user.organization,
                    product=self.stock_io_log.stock.product,
                    store_point=self.store
                )
            )
            stock_1.append(stock)
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
        length = len(request.data[0]['stock'])
        stock_amount = 0
        stock_amount_request = 0
        for item in range(0, random_counter):
            stock_amount += stock_1[item].quantity
            stock_amount_request += request.data[0]['stock'][item]['quantity']

        self.assertEqual(length, random_counter)
        self.assertEqual(stock_amount_request, stock_amount)

        for item in range(0, random_counter):
            StockIOLogFactory.create_batch(
                1, organization=self.admin_user.organization, sales=None,
                expire_date=None, type=StockIOType.OUT, batch=stock_1[item].batch,
                quantity=quantity, date=str(self.date_to_find),
                stock=stock_1[item].stock
            )

        # calling the api
        request = self.client.get(self.url)
        self.assertSuccess(request)
        length = len(request.data[0]['stock'])
        stock_amount = 0
        stock_amount_request = 0
        for item in range(random_counter, random_counter * 2):
            stock_amount_request += request.data[0]['stock'][item]['quantity']

        self.assertEqual(length, random_counter * 2)
        self.assertEqual(stock_amount_request, stock_amount)

        # admin user logout
        self.client.logout()
