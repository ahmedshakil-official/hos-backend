import random
from datetime import date

from faker import Faker
from django.urls import reverse
from common.enums import Status
from common.test_case import OmisTestCase
from ..tests import StorePointFactory, SalesFactory, StockIOLogFactory, StockFactory


class SalesVatReportAPITest(OmisTestCase):
    url = reverse('pharmacy.product.sales-vat-report')
    fake = Faker()

    def test_sales_vat_report_get(self):

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

        # ===========================================
        #  User logout
        # ===========================================
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)

        # ===========================================
        #  Fetch successful
        # ===========================================
        self.assertSuccess(request)
        StorePointFactory(
            organization=self.admin_user.organization
        )
        sales = SalesFactory(
            organization=self.admin_user.organization,
            status=Status.ACTIVE
        )
        stock = StockFactory(
            organization=self.admin_user.organization,
            store_point=sales.store_point,
            status=Status.ACTIVE
        )
        date_0 = self.fake.date()
        date_1 = date.today()
        stock_io_log = StockIOLogFactory.create_batch(
            5,
            organization=self.admin_user.organization,
            stock=stock,
            date=date_0,
            sales=sales,
            vat_total=random.randint(5, 10),
            status=Status.ACTIVE
        )
        quantity = 0
        vat_total = 0
        discount_total = 0
        round_discount = 0
        for item in stock_io_log:
            rate = item.rate
            quantity += item.quantity
            vat_total += item.vat_total
            discount_total += item.discount_total
            round_discount += item.round_discount

        total_sales = float(rate * quantity +
                            vat_total - discount_total + round_discount)
        total_vat = float(vat_total)
        base_sales = float(rate * quantity)
        vat_rate = float((total_vat * 100) / base_sales)

        data = {
            'date_0': date_0,
            'date_1': date_1,
            'store_points': sales.store_point.alias
        }

        request = self.client.get(self.url, data)
        self.assertSuccess(request)
        self.assertEqual(total_sales, request.data[0]['total_sales'])
        self.assertEqual(total_vat, request.data[0]['total_vat'])
        self.assertEqual(vat_rate, request.data[0]['vat_rate'])
        self.client.logout()
