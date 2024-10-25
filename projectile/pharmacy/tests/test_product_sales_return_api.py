import json
import random
import dateutil.parser
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from common.utils import get_timezone_aware_current_time
from core.tests import PersonFactory, EmployeeFactory, SupplierFactory
from common.enums import Status

from ..tests import PurchaseFactory, StockFactory, ProductFactory
from ..models import Purchase, StockIOLog


class ProductSalesReturnListAPITest(OmisTestCase):
    url = reverse('pharmacy.sales-return-list')
    fake = Faker()

    def setUp(self):
        super(ProductSalesReturnListAPITest, self).setUp()

    def test_sales_return_list_get(self):
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

        purchase_will_be_deleted = PurchaseFactory.create_batch(
            2, organization=self.admin_user.organization,
            is_sales_return=True, status=Status.ACTIVE)

        num_of_sales_return = [item for item in purchase_will_be_deleted
                               if item.is_sales_return == True]
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(len(request.data['results']), len(num_of_sales_return))

        purchase_will_be_deleted[0].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)
        self.assertEqual(len(request.data['results']), 1)

        # admin user logout
        self.client.logout()

    def test_sales_return_list_post(self):
        # ===========================================
        #  Check without login
        # ===========================================
        stock = StockFactory(
            organization=self.admin_user.organization,
            product=ProductFactory(is_service=False)
        )
        stock_before = stock.stock
        supplier = SupplierFactory(organization=self.admin_user.organization)
        data = {
            "purchase_date": str(get_timezone_aware_current_time()),
            "supplier": supplier.pk,
            "amount": random.randint(50, 100),
            "discount": random.randint(10, 100),
            "receiver": EmployeeFactory(organization=self.admin_user.organization).pk,
            "remarks": self.fake.text(128),
            "transport": random.randint(10, 15),
            "is_sales_return": random.choice([True, False]),
            "stock_io_logs": [
                {
                    "stock": stock.pk,
                    "quantity": random.randint(1, 10),
                    "rate": random.randint(1, 3),
                    "batch": self.fake.text(128)
                },
                {
                    "stock": stock.pk,
                    "quantity": random.randint(1, 10),
                    "rate": random.randint(1, 3),
                    "batch": self.fake.text(128)
                }
            ]
        }

        data['grand_total'] = sum([
            item.get('rate') * item.get('quantity')
            for item in data["stock_io_logs"]
        ])

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
        request = self.client.post(
            self.url, data=json.dumps(dict(data)),
            content_type='application/json'
        )
        self.assertCreated(request)
        self.assertEqual(Purchase.objects.count(), 1)
        self.assertEqual(StockIOLog.objects.count(), 2)

        # check if the stock is adjusting accordingly
        old_stock = stock.stock
        stock.refresh_from_db()
        self.assertEqual(old_stock + (data['stock_io_logs'][0]['quantity'] +
                                      data['stock_io_logs'][1]['quantity']), stock.stock)

        # total = 0
        # for item in data['stock_io_logs']:
        #     total += item['quantity'] * item['rate']

        # if total != data['amount']:
        #     data['amount'] = total

        # check if the supplier's balance is changing accordingly
        old_balance = supplier.balance
        supplier.refresh_from_db()
        # self.assertEqual(old_balance + (data['amount'] - data['discount'] +
        #                                 data['transport']), supplier.balance)
        self.assertEqual(str(dateutil.parser.parse(request.data['purchase_date'])), data['purchase_date'])
        self.assertEqual(request.data['supplier'], data['supplier'])
        self.assertEqual(request.data['amount'], data['amount'])
        self.assertEqual(request.data['discount'], data['discount'])
        self.assertEqual(request.data['receiver'], data['receiver'])
        self.assertEqual(request.data['transport'], data['transport'])
        self.assertEqual(request.data['remarks'], data['remarks'])
        self.assertEqual(request.data['is_sales_return'], data['is_sales_return'])

        # admin user logout
        self.client.logout()


class ProductSalesReturnDetailsAPITest(OmisTestCase):

    def setUp(self):
        super(ProductSalesReturnDetailsAPITest, self).setUp()

        # set a appointment treatment session
        self.admin_user_product_purchase = PurchaseFactory(
            organization=self.admin_user.organization,
            status=Status.ACTIVE,
            is_sales_return=True)

        # set the url
        self.url = reverse('pharmacy.sales-return.details',
                           args=[self.admin_user_product_purchase.alias])

    def test_product_sales_return_details_get(self):
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
        # if self.admin_user_product_purchase.is_sales_return:
        #     self.assertNotFound(request)
        # else:
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        if self.admin_user_product_purchase.is_sales_return:
            self.assertEqual(
                request.data['id'], self.admin_user_product_purchase.id)
        else:
            self.assertNotFound(request)

        # admin user logout
        self.client.logout()
