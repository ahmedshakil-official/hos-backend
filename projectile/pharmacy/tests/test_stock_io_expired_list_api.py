import random
import datetime
from faker import Faker

from django.urls import reverse
from common.test_case import OmisTestCase
from ..tests import (
    StockFactory,
    StockIOLogFactory,
    StorePointFactory,
)
from ..enums import StockIOType


class StockIOExpiredListAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(StockIOExpiredListAPITest, self).setUp()

    def test_stock_expired_list_get(self):
        date_to_find = datetime.date.today() + datetime.timedelta(days=2)
        store = StorePointFactory(organization=self.admin_user.organization)
        date = str(date_to_find)
        dates = date.split("-")
        url = reverse('pharmacy.stock-list-expire', args=[store.id, dates[0], dates[1], dates[2]])
        random_counter = random.randint(5, 6)
        quantity = random.randint(4, 6)
        stock_1 = StockIOLogFactory.create_batch(
            random_counter, organization=self.admin_user.organization,
            expire_date=str(date_to_find), quantity=quantity, purchase=None,
            stock=StockFactory(
                organization=self.admin_user.organization, store_point=store
            )
        )
        StockIOLogFactory.create_batch(
            random_counter, organization=self.admin_user.organization, purchase=None,
            expire_date=str(date_to_find + datetime.timedelta(days=2)), quantity=quantity,
            stock=StockFactory(
                organization=self.admin_user.organization, store_point=store
            )
        )

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(url)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        # calling the api
        request = self.client.get(url)
        self.assertSuccess(request)
        length = len(request.data)
        self.assertEqual(length, random_counter)

        StockIOLogFactory.create_batch(
            random_counter, organization=self.admin_user.organization,
            expire_date=str(date_to_find), quantity=quantity, purchase=None,
            stock=StockFactory(
                organization=self.admin_user.organization, store_point=store
            )
        )

        request = self.client.get(url)
        self.assertSuccess(request)
        length2 = len(request.data)
        self.assertEqual(length2, 2 * random_counter)

        for item in range(0, length):
            StockIOLogFactory.create_batch(
                1, organization=self.admin_user.organization, sales=None,
                expire_date=None, type=StockIOType.OUT, batch=stock_1[item].batch,
                quantity=quantity,
                stock=stock_1[item].stock
            )

        request = self.client.get(url)
        self.assertSuccess(request)
        self.assertEqual(len(request.data), random_counter)

        # admin user logout
        self.client.logout()
