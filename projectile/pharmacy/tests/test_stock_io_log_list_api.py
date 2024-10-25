import random
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase

from ..tests import StockFactory, ProductFactory, StockIOLogFactory, PurchaseFactory
from ..models import StockIOLog
from ..enums import StockIOType


class StockIOLogListAPITest(OmisTestCase):
    url = reverse('pharmacy.stock-io-log-list')
    fake = Faker()

    def setUp(self):
        super(StockIOLogListAPITest, self).setUp()

    def test_stock_io_log_list_get(self):
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

        stock = StockFactory(
            product=ProductFactory(organization=self.admin_user.organization, is_service=False),
            organization=self.admin_user.organization
        )
        stock_io_log = StockIOLogFactory.create_batch(
            2,
            stock=stock,
            organization=self.admin_user.organization
        )

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        stock_io_log[0].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)

    #     # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        StockFactory()
        request = self.client.get(self.url)
        self.assertSuccess(request)

    #     # check if it is the same user
        self.assertEqual(request.data['count'], 1)
        self.assertEqual(request.data['results'][0]['id'], stock_io_log[1].id)
        self.assertEqual(request.data['results'][0]['alias'], str(stock_io_log[1].alias))
        self.assertEqual(request.data['results'][0]['quantity'], stock_io_log[1].quantity)

    #     # admin user logout
        self.client.logout()

    def test_stock_io_log_list_post(self):
        # Create data for stock_io_log
        data = {
            'quantity': random.randint(1, 5),
            'rate': random.randint(10, 15),
            'batch': self.fake.first_name(),
            'expire_date': self.fake.date(),
            'date': self.fake.date(),
            'type': StockIOType.INPUT,
            'purchase': PurchaseFactory().pk,
            'stock': StockFactory().pk
        }
        # ===========================================
        #  Check without login
        # ===========================================

        request = self.client.post(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.post(self.url, data)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.post(self.url, data)
        self.assertCreated(request)
        self.assertEqual(StockIOLog.objects.count(), 1)
        self.assertEqual(request.data['quantity'], data['quantity'])
        self.assertEqual(request.data['rate'], data['rate'])
        self.assertEqual(request.data['batch'], data['batch'].upper())

        # admin user logout
        self.client.logout()
