from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase

from ..tests import StockFactory, ProductFactory


class SalesAbleStockProductListAPITest(OmisTestCase):
    url = ''
    fake = Faker()

    def setUp(self):
        super(SalesAbleStockProductListAPITest, self).setUp()

    def test_sales_able_stock_product_list_get(self):
        stock = StockFactory.create_batch(
            2,
            product=ProductFactory(organization=self.admin_user.organization, is_service=False),
            organization=self.admin_user.organization
        )

        self.url = reverse(
            'pharmacy.sales-able-stock-product.list',
            args=[stock[0].store_point.alias]
        )

        data = {
            'keyword': ''
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.get(self.url, data)
        self.assertSuccess(request)

        if stock[0].product.is_salesable:
            self.assertEqual(request.data['count'], 1)
        else:
            self.assertEqual(request.data['count'], 0)

        stock[0].delete()

        # test with one entry with same user
        stock2 = StockFactory(
            organization=self.admin_user.organization,
            product=ProductFactory(organization=self.admin_user.organization, is_service=False)
        )
        self.url = reverse('pharmacy.sales-able-stock-product.list',
                           args=[stock2.store_point.alias])
        request = self.client.get(self.url, data)
        self.assertSuccess(request)

        # check if it is the same user
        if stock2.product.is_salesable == True:
            self.assertEqual(len(request.data['results']), 1)
        else:
            self.assertEqual(len(request.data['results']), 0)

        # admin user logout
        self.client.logout()
