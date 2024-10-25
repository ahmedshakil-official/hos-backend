import json
import random
from faker import Faker
from dateutil.parser import parse

from django.urls import reverse


from common.test_case import OmisTestCase
from common.utils import get_timezone_aware_current_time
from common.enums import Status
from core.tests import EmployeeFactory, SupplierFactory, DepartmentFactory

from ..tests import PurchaseFactory, StockFactory, StorePointFactory
from ..models import Purchase, StockIOLog


class ProductPurchaseListAPITest(OmisTestCase):
    url = reverse('pharmacy.purchase-list')
    fake = Faker()

    def setUp(self):
        super(ProductPurchaseListAPITest, self).setUp()

    def test_purchase_list_get(self):
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
            2, organization=self.admin_user.organization
        )

        num_of_purchase = [item for item in purchase_will_be_deleted
                           if item.is_sales_return == False and item.status == Status.ACTIVE]
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(len(request.data['results']), len(num_of_purchase))

        purchase_will_be_deleted[0].delete()
        num_of_purchase = [item for item in purchase_will_be_deleted \
            if item.is_sales_return == False and item.status == Status.ACTIVE]

        self.assertEqual(len(request.data['results']), len(num_of_purchase))

        # PurchaseFactory()
        # request = self.client.get(self.url)
        # self.assertSuccess(request)

        # check if it is the same user
        # if PurchaseFactory().is_sales_return:
        #     self.assertEqual(len(request.data['results']), 0)
        # else:
        #     self.assertEqual(len(request.data['results']), 1)

        # admin user logout
        self.client.logout()

    def test_purchase_list_post(self):
        # ===========================================
        #  Check without login
        # ===========================================
        store_point = StorePointFactory(organization=self.admin_user.organization)
        stock = StockFactory(
            organization=self.admin_user.organization,
            store_point=store_point
        )
        stock_before = stock.stock
        supplier = SupplierFactory(organization=self.admin_user.organization)
        department = DepartmentFactory(organization=self.admin_user.organization)
        requisitions = PurchaseFactory.create_batch(
            2,
            amount=random.randint(500, 1000),
            organization=self.admin_user.organization, status=Status.DRAFT,
        )
        data = {
            "status": Status.ACTIVE,
            "purchase_date": str(get_timezone_aware_current_time()),
            "requisition_date": self.fake.date(),
            "supplier": supplier.pk,
            'store_point': store_point.pk,
            "department": department.pk,
            "amount": random.randint(50, 100),
            "discount": random.randint(10, 100),
            "vat_rate": random.randint(1, 50),
            "tax_rate": random.randint(1, 50),
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
            ],
            "requisitions": [requisition.id for requisition in requisitions]
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
        self.assertEqual(Purchase.objects.filter(status=Status.ACTIVE).count(), 1)
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

        # calculation of tax_total, vat_total and grand_total
        tax_total = (data['amount'] - data['discount']) * data['tax_rate'] / 100.0
        # limiting decimal places
        self.assertEqual(request.data['tax_total'], round(tax_total, 2))

        vat_total = (data['amount'] * data['vat_rate']) / 100.0
        self.assertEqual(request.data['vat_total'], round(vat_total, 2))

        grand_total = (data['amount'] - data['discount']) + tax_total + vat_total
        self.assertEqual(request.data['grand_total'], round(grand_total, 2))
        # check if the supplier's balance is changing accordingly
        old_balance = supplier.balance
        new_balance = old_balance + grand_total + data['transport']
        requisition_count = Purchase.objects.get(
            pk=request.data['id']).requisitions.count()
        supplier.refresh_from_db()
        # self.assertEqual(round(new_balance, 2), round(supplier.balance, 2))
        self.assertEqual(request.data['status'], data['status'])
        self.assertEqual(str(parse(request.data['purchase_date'])), (data['purchase_date']))
        self.assertEqual(request.data['requisition_date'], data['requisition_date'])
        self.assertEqual(request.data['supplier'], data['supplier'])
        self.assertEqual(request.data['amount'], data['amount'])
        self.assertEqual(request.data['discount'], data['discount'])
        self.assertEqual(request.data['vat_rate'], data['vat_rate'])
        self.assertEqual(request.data['tax_rate'], data['tax_rate'])
        self.assertEqual(request.data['receiver'], data['receiver'])
        self.assertEqual(request.data['transport'], data['transport'])
        self.assertEqual(request.data['remarks'], data['remarks'])
        self.assertEqual(request.data['is_sales_return'], data['is_sales_return'])
        self.assertEqual(requisition_count, len(requisitions))

        # admin user logout
        self.client.logout()


class ProductPurchaseDetailsAPITest(OmisTestCase):
    url = None
    fake = Faker()

    def setUp(self):
        super(ProductPurchaseDetailsAPITest, self).setUp()

        # set a appointment treatment session
        self.admin_user_product_purchase = PurchaseFactory(
            organization=self.admin_user.organization, status=Status.ACTIVE, is_sales_return=False)

        # set the url
        self.url = reverse('pharmacy.purchase-details',
                           args=[self.admin_user_product_purchase.alias])

    def test_product_purchase_details_get(self):
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
        self.assertEqual(
            request.data['id'], self.admin_user_product_purchase.id)

        # admin user logout
        self.client.logout()

    def test_product_purchase_details_delete(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.delete(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.delete(self.url)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        self.assertEqual(Purchase.objects.count(), 1)
        request = self.client.delete(self.url)
        self.assertDeleted(request)

        # admin user logout
        self.client.logout()

    def test_product_purchase_details_patch(self):
        data = {
            'status': Status.INACTIVE
        }
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.patch(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.patch(self.url, data)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        self.assertEqual(Purchase.objects.count(), 1)
        request = self.client.patch(self.url,
                                    data=json.dumps(dict(data)), content_type='application/json')
        self.assertEqual(request.data['status'], data['status'])

        # admin user logout
        self.client.logout()
