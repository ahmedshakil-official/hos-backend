import random
from faker import Faker
import urllib.parse

from django.urls import reverse
from common.test_case import OmisTestCase
from pharmacy.models import Stock
from pharmacy.utils import stock_specific_attribute_filter
from ..tests import (
    StorePointFactory,
    ProductFactory,
    ProductGroupFactory,
    ProductFormFactory,
    ProductSubGroupFactory,
    ProductManufacturingCompanyFactory,
)

class StockBulkUpdateAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(StockBulkUpdateAPITest, self).setUp()
        self.url = reverse('pharmacy.stock-bulk-update')
        self.salesable_stock_list_url = ''

    def test_stock_bulk_update(self):
        product_companies = ProductManufacturingCompanyFactory.create_batch(
            2,
            organization=self.admin_user.organization
        )

        product_forms = ProductFormFactory.create_batch(
            2,
            organization=self.admin_user.organization
        )

        product_groups = ProductGroupFactory.create_batch(
            2,
            organization=self.admin_user.organization
        )

        product_sub_groups = ProductSubGroupFactory.create_batch(
            2,
            organization=self.admin_user.organization,
            product_group=random.choice(product_groups)
        )

        store_points = StorePointFactory.create_batch(
            2,
            organization=self.admin_user.organization
        )

        product_factory = ProductFactory.create_batch(
            5,
            organization=self.admin_user.organization,
            manufacturing_company=random.choice(product_companies),
            form=random.choice(product_forms),
            subgroup=random.choice(product_sub_groups),
            is_service=False,
            is_salesable=True
        )

        # make sure stock value is more than Zero (0) for salesable stock list
        for stock in Stock.objects.filter():
            stock.stock = random.randint(100, 1000)
            stock.save()

        query_params = {
            'store_points': store_points[0].alias,
            'products': product_factory[0].alias,
            'companies': product_factory[0].manufacturing_company.alias,
            'product_forms': product_factory[0].form.alias,
            'product_subgroups': product_factory[0].subgroup.alias,
            'product_groups': product_factory[0].subgroup.product_group.alias,
        }

        data = {
            'discount_margin': random.randint(10, 20),
            'rack': self.fake.first_name(),
            'minimum_stock': random.randint(100, 1000),
        }

        # ===========================================
        #  Check without login
        # ===========================================
        url = "{}?{}".format(self.url, urllib.parse.urlencode(query_params))
        request = self.client.patch(url, data)
        self.assertPermissionDenied(request)

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

        request = self.client.patch(url, data)
        self.assertSuccess(request)

        stocks_in_db = Stock.objects.filter(
            **stock_specific_attribute_filter(query_params)
        )
        self.assertEqual(request.data['count'], stocks_in_db.count())

        # *************** check salesable stock list ********
        # **************** if values updated properlly ******
        self.salesable_stock_search_url = reverse(
            'pharmacy.sales-able-stock-product.list',
            args=[str(query_params['store_points'])]
        )
        stock_request = self.client.get(
            self.salesable_stock_search_url,
            {'product': query_params['products']})

        self.assertSuccess(stock_request)
        # match with individual stock's field
        self.assertEqual(stock_request.data['results'][0]['rack'], data['rack'])
        self.assertEqual(
            stock_request.data['results'][0]['minimum_stock'], data['minimum_stock'])
        self.assertEqual(
            stock_request.data['results'][0]['discount_margin'], data['discount_margin'])
        # ===========================================
        #  update second storepoint's all stock
        # ===========================================

        query_params = {
            'store_points': store_points[1].alias,
        }

        data2 = {
            'discount_margin': random.randint(10, 20),
            'rack': self.fake.first_name(),
            'minimum_stock': random.randint(100, 1000),
        }

        url = "{}?{}".format(self.url, urllib.parse.urlencode(query_params))
        request = self.client.patch(url, data2)
        self.assertSuccess(request)

        stocks_in_db = Stock.objects.filter(
            **stock_specific_attribute_filter(query_params)
        )

        self.assertEqual(request.data['count'], stocks_in_db.count())

        # *************** check salesable stock list ********
        # **************** if values updated properly ******
        self.salesable_stock_search_url = reverse(
            'pharmacy.sales-able-stock-product.list',
            args=[str(query_params['store_points'])]
        )
        stock_request = self.client.get(self.salesable_stock_search_url)
        self.assertSuccess(stock_request)

        # match with individual stock's field
        for item in stock_request.data['results']:
            self.assertEqual(item['rack'], data2['rack'])
            self.assertEqual(item['minimum_stock'], data2['minimum_stock'])
            self.assertEqual(item['discount_margin'], data2['discount_margin'])

        # ===========================================
        #  update first storepoint's stock which matched with
        #  product_group, companies, product_form, 'product_subgroups one by one
        # ===========================================

        query_criterias = [
            'product_groups', 'companies', 'product_forms', 'product_subgroups'
        ]

        all_query = {
            'companies': product_factory[0].manufacturing_company.alias,
            'product_forms': product_factory[0].form.alias,
            'product_subgroups': product_factory[0].subgroup.alias,
            'product_groups': product_factory[0].subgroup.product_group.alias,
        }

        for criteria in query_criterias:
            query = {
                'store_points': store_points[0].alias,
            }

            query[criteria] = all_query[criteria]

            data3 = {
                'discount_margin': random.randint(15, 20),
                'rack': self.fake.first_name(),
                'minimum_stock': random.randint(100, 1000),
            }

            url = "{}?{}".format(self.url, urllib.parse.urlencode(query))

            request = self.client.patch(url, data3)

            self.assertSuccess(request)

            stocks_in_db = Stock.objects.filter(
                **stock_specific_attribute_filter(query)
            )

            self.assertEqual(request.data['count'], stocks_in_db.count())

            # match with individual stock's field
            for item in stocks_in_db:
                self.assertEqual(item.rack, data3['rack'])
                self.assertEqual(item.minimum_stock, data3['minimum_stock'])
                self.assertEqual(item.discount_margin, data3['discount_margin'])

        # admin user logout
        self.client.logout()
