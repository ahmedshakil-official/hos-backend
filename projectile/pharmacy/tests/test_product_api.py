import json
import random
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase

from ..tests import (
    ProductFactory,
    ProductManufacturingCompanyFactory,
    ProductSubGroupFactory,
    StockFactory,
    StorePointFactory,
    UnitFactory,
    ProductCategoryFactory,
)
from ..models import Product


class ProductListAPITest(OmisTestCase):
    url = reverse('pharmacy.product.list')
    fake = Faker()

    def setUp(self):
        super(ProductListAPITest, self).setUp()

    def test_product_list_get(self):
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

        product_will_be_deleted = ProductFactory.create_batch(2, organization=self.admin_user.organization)

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        product_will_be_deleted[0].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        ProductFactory()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # admin user logout
        self.client.logout()

    def test_product_list_post(self):
        # ===========================================
        #  Check without login
        # ===========================================
        data = {
            'name': self.fake.first_name(),
            'strength': self.fake.first_name(),
            'trading_price': random.randint(10, 12),
            'purchase_price': random.randint(8, 10),
            'manufacturing_company': ProductManufacturingCompanyFactory().pk,
            'subgroup': ProductSubGroupFactory().pk,
            'is_salesable': random.choice([True, False]),
            'is_printable': random.choice([True, False]),
            'primary_unit': UnitFactory().pk,
            'secondary_unit': UnitFactory().pk,
            'conversion_factor': random.randint(10, 12),
            'category': ProductCategoryFactory().pk
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
        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['strength'], data['strength'])
        self.assertEqual(request.data['trading_price'], data['trading_price'])
        self.assertEqual(request.data['purchase_price'], data['purchase_price'])
        self.assertEqual(request.data['manufacturing_company'], data['manufacturing_company'])
        self.assertEqual(request.data['subgroup'], data['subgroup'])
        self.assertEqual(request.data['is_salesable'], data['is_salesable'])
        self.assertEqual(request.data['is_printable'], data['is_printable'])
        self.assertEqual(request.data['primary_unit'], data['primary_unit'])
        self.assertEqual(request.data['secondary_unit'], data['secondary_unit'])
        self.assertEqual(request.data['conversion_factor'], data['conversion_factor'])
        self.assertEqual(request.data['category'], data['category'])
        self.assertEqual(Product.objects.count(), 1)

        # admin user logout
        self.client.logout()


class ProductDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(ProductDetailsAPITest,self).setUp()

        # set a product
        self.product = ProductFactory(
            organization=self.admin_user.organization)

        # set the url
        self.url = reverse('pharmacy.product.details', args=[self.product.alias])

    def test_product_details_get(self):
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
        # self.assertPermissionDenied(request)

        # # ===========================================
        # #  Check with admin user of same organization
        # # ===========================================
        # self.admin_user.organization = self.user.organization
        # self.admin_user.save()
        # request = self.client.get(self.url)
        self.assertSuccess(request)
        self.assertEqual(request.data['id'], self.product.id)

        # admin user logout
        self.client.logout()

    def test_product_details_put(self):
        data = {
            'name': self.fake.first_name(),
            'strength': self.fake.first_name(),
            'trading_price': random.randint(10, 12),
            'purchase_price': random.randint(8, 10),
            'manufacturing_company': ProductManufacturingCompanyFactory().pk,
            'subgroup': ProductSubGroupFactory().pk,
            'is_salesable': random.choice([True, False]),
            'is_printable': random.choice([True, False]),
            'primary_unit': UnitFactory().pk,
            'secondary_unit': UnitFactory().pk,
            'conversion_factor': random.randint(10, 12),
            'category': ProductCategoryFactory().pk
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
        request = self.client.put(self.url, data=json.dumps(dict(data)), content_type='application/json')
        # self.assertPermissionDenied(request)

        # # ===========================================
        # #  Check with admin user of same organization
        # # ===========================================
        # self.admin_user.organization = self.user.organization
        # self.admin_user.save()
        # request = self.client.put(self.url, data=json.dumps(dict(data)), content_type='application/json')
        self.assertSuccess(request)
        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['strength'], data['strength'])
        self.assertEqual(request.data['trading_price'], data['trading_price'])
        self.assertEqual(request.data['purchase_price'], data['purchase_price'])
        self.assertEqual(request.data['manufacturing_company'], data['manufacturing_company'])
        self.assertEqual(request.data['subgroup'], data['subgroup'])
        self.assertEqual(request.data['is_salesable'], data['is_salesable'])
        self.assertEqual(request.data['is_printable'], data['is_printable'])
        self.assertEqual(request.data['primary_unit'], data['primary_unit'])
        self.assertEqual(request.data['secondary_unit'], data['secondary_unit'])
        self.assertEqual(request.data['conversion_factor'], data['conversion_factor'])
        self.assertEqual(request.data['category'], data['category'])

        # admin user logout
        self.client.logout()


class ProductStockAPITest(OmisTestCase):
    url = None
    fake = Faker()

    def setUp(self):
        super(ProductStockAPITest,self).setUp()

        # set a product
        self.product = ProductFactory(organization=self.user.organization)
        self.stock = StockFactory(organization=self.user.organization, product=self.product)

        # set the url
        self.url = reverse('pharmacy.product-stock-list', args=[self.product.alias])

    def test_product_stock_get(self):
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
        self.assertSuccess(request)
        # check if it is the same user
        self.assertEqual(len(request.data), 0)

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)
        self.assertEqual(len(request.data), 1)

        self.assertEqual(request.data[0]['id'], self.stock.id)
        self.assertEqual(request.data[0]['alias'], str(self.stock.alias))
        self.assertEqual(request.data[0]['tracked'], self.stock.tracked)
        self.assertEqual(request.data[0]['discount_margin'], self.stock.discount_margin)

        # admin user logout
        self.client.logout()


class ProductListStockUnderDemandAPITest(OmisTestCase):
    url = reverse('pharmacy.product-list-stock-inder-demand')
    fake = Faker()

    def setUp(self):
        super(ProductListStockUnderDemandAPITest, self).setUp()

    def test_product_list_stock_under_demand_get(self):
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


        request = self.client.get(self.url)
        self.assertSuccess(request)

        request = self.client.get(self.url)
        self.assertSuccess(request)

        stock_amount = random.randint(10, 200)
        demand_amount = random.randint(300, 1000)
        store_point = StorePointFactory(organization=self.admin_user.organization)
        product = ProductFactory(organization=self.admin_user.organization)
        StockFactory(
            organization=self.admin_user.organization,
            store_point=store_point, product=product, stock=stock_amount, demand=demand_amount)
        StockFactory(
            organization=self.admin_user.organization,
            store_point=store_point, product=product, stock=demand_amount, demand=stock_amount)

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # compare the created data with request data
        # it should return 1 as one object's stock is greter than demand
        self.assertEqual(request.data['count'], 1)

        # admin user logout
        self.client.logout()
