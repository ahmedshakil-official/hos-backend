import random
import datetime
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase

from ..tests import (StockIOLogFactory,
                     StockFactory,
                     StorePointFactory,
                     ProductFactory, )


class StockIOLogInputOutputListAPITest(OmisTestCase):
    # url = reverse('pharmacy.stock-io-log-list-by-store')
    fake = Faker()
    store_point = None
    product = None

    def setUp(self):
        super(StockIOLogInputOutputListAPITest, self).setUp()

        self.store_point = StorePointFactory(organization=self.admin_user.organization)
        self.product = ProductFactory(organization=self.admin_user.organization)

        self.year = random.randint(2001, 2017)
        self.start_year = random.randint(2001, 2017)
        self.start_month = random.randint(1, 12)
        self.start_day = random.randint(1, 28)
        self.end_year = self.start_year + random.randint(1, 5)
        self.end_month = random.randint(1, 12)
        self.end_day = random.randint(1, 28)

        self.url = reverse('pharmacy.stock-io-log-list-by-store',
                           args=[self.store_point.alias, self.product.alias])
        self.data = {
            'from': "{}-{}-{}".format(self.start_day, self.start_month, self.start_year),
            'to': "{}-{}-{}".format(self.end_day, self.end_month, self.end_year)
        }

    def test_stock_io_log_input_output_list_get(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, self.data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, self.data)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        # creating entry
        date_str = "{}-{}-{}".format(self.start_day, self.start_month, self.start_year)
        date = datetime.datetime.strptime(date_str, '%d-%m-%Y').date()
        date_to_find = str(date)
        StockIOLogFactory.create_batch(5, organization=self.admin_user.organization,
                                       stock=StockFactory(organization=self.admin_user.organization,
                                                          product=self.product, store_point=self.store_point),
                                       date=date_to_find)

        # calling the api
        request = self.client.get(self.url, self.data)
        self.assertSuccess(request)
        self.assertEqual(request.data['count'], 5)

        # creating entry
        self.input_year = self.end_year + random.randint(1, 5)
        date_str = "{}{}{}".format(self.end_day, self.end_month, self.input_year)
        date = datetime.datetime.strptime(date_str, '%d%m%Y').date()
        date_to_find = str(date)
        StockIOLogFactory.create_batch(5, organization=self.admin_user.organization,
                                       stock=StockFactory(organization=self.admin_user.organization,
                                                          product=self.product, store_point=self.store_point),
                                       date=date_to_find)

        # calling the api
        request = self.client.get(self.url, self.data)
        self.assertSuccess(request)
        self.assertEqual(request.data['count'], 5)
        
        self.data = {
            'from': "{}-{}-{}".format(self.start_day, self.start_month, self.start_year),
            'to': "{}-{}-{}".format(self.end_day, self.end_month, self.input_year)
        }

        # calling the api
        request = self.client.get(self.url, self.data)
        self.assertSuccess(request)
        self.assertEqual(request.data['count'], 10)

        # admin user logout
        self.client.logout()
