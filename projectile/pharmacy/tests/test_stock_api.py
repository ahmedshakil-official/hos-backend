import json
import random
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status

from ..tests import StockFactory, ProductFactory, StorePointFactory, StockIOLogFactory
from ..models import Stock
from ..enums import StockIOType


class StockListAPITest(OmisTestCase):
    url = reverse('pharmacy.stock-list')
    fake = Faker()

    def setUp(self):
        super(StockListAPITest, self).setUp()

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

        stock_will_be_deleted = StockFactory.create_batch(
            2,
            product=ProductFactory(organization=self.admin_user.organization, is_service=False),
            organization=self.admin_user.organization
        )

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        stock_will_be_deleted[0].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        StockFactory()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # admin user logout
        self.client.logout()

    def test_stock_list_post(self):
        # ===========================================
        #  Check without login
        # ===========================================
        data = {
            'product': ProductFactory().pk,
            'store_point': StorePointFactory().pk,
            'stock': random.randint(0, 1000),
            'auto_adjustment': random.choice([True, False])
        }
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
        self.assertEqual(Stock.objects.count(), 1)
        self.assertEqual(request.data['product'], data['product'])
        self.assertEqual(request.data['store_point'], data['store_point'])
        self.assertEqual(request.data['stock'], data['stock'])
        self.assertEqual(request.data['auto_adjustment'], data['auto_adjustment'])

        # admin user logout
        self.client.logout()


class StockDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(StockDetailsAPITest, self).setUp()

        # set a product
        self.stock = StockFactory(
            product=ProductFactory(organization=self.admin_user.organization),
            organization=self.user.organization
        )

        # set the url
        self.url = reverse('pharmacy.stock-details', args=[self.stock.alias])

    def test_stock_details_get(self):
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
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)
        self.assertEqual(request.data['id'], self.stock.id)

        # admin user logout
        self.client.logout()

    def test_stock_details_put(self):
        data = {
            'product': ProductFactory().pk,
            'store_point': StorePointFactory().pk,
            'stock': random.randint(0, 1000),
            'auto_adjustment': random.choice([True, False])
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
        request = self.client.put(
            self.url, data=json.dumps(dict(data)), content_type='application/json')
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.put(
            self.url, data=json.dumps(dict(data)), content_type='application/json')
        self.assertSuccess(request)
        self.assertEqual(request.data['product'], data['product'])
        self.assertEqual(request.data['store_point'], data['store_point'])
        self.assertEqual(request.data['stock'], data['stock'])
        self.assertEqual(request.data['auto_adjustment'], data['auto_adjustment'])

        # admin user logout
        self.client.logout()


class StockDemandSignalTest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(StockDemandSignalTest, self).setUp()

    def test_stock_demand_signal(self):

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        stock_demand = random.randint(1, 100)
        stock = StockFactory(
            product=ProductFactory(organization=self.user.organization),
            organization=self.user.organization, demand=stock_demand
        )

        previous_demand = stock.demand
        StockIOLogFactory(
            organization=self.user.organization,
            type=StockIOType.INPUT, status=Status.DRAFT, stock=stock)
        stock.refresh_from_db()
        self.assertEqual(stock.demand, previous_demand * 2)

        StockIOLogFactory(
            organization=self.user.organization,
            type=StockIOType.INPUT, status=Status.RELEASED, stock=stock)
        stock.refresh_from_db()
        self.assertEqual(stock.demand, 0)

        # admin user logout
        self.client.logout()
