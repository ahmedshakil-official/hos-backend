import json
import random
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from core.tests import PersonFactory, EmployeeFactory

from ..tests import StockFactory, StockTransferFactory, StorePointFactory
from ..models import StockIOLog, StockTransfer
from ..enums import StockIOType, TransferStatusType
from common.enums import Status


class StockTransferRequisitionListAPITest(OmisTestCase):
    url = reverse('pharmacy.stock-transfer-requisition')
    fake = Faker()

    def test_stock_transfer_list_get(self):
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

        sales_will_be_deleted = StockTransferFactory.create_batch(5, organization=self.admin_user.organization)
        stocks = [item for item in sales_will_be_deleted
        if item.status == Status.DRAFT]

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], len(stocks))

        sales_will_be_deleted[0].delete()

        # check if it is the same user
        rest_of_stocks = StockTransfer.objects.filter(status=Status.DRAFT)

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], len(rest_of_stocks))

        # admin user logout
        self.client.logout()


class StockTransferRequisitionListPostAPITest(OmisTestCase):
    url = reverse('pharmacy.stock-transfer')
    fake = Faker()

    def test_stock_transfer_requisition_list_post(self):
        # ===========================================
        #  Check without login
        # ===========================================
        # new stock for in
        stock_in = StockFactory(organization=self.admin_user.organization)
        # new stock for out
        stock_out = StockFactory(
            organization=self.admin_user.organization,
            product=stock_in.product
        )
        # assign stock in to a variable
        stock_in_before = stock_in.stock
        # assign stock out to a variable
        stock_out_before = stock_out.stock
        data = {
            "status": Status.DRAFT,
            "date": str(self.fake.date()),
            "transfer_from": stock_in.store_point.pk,
            "transfer_to": stock_out.store_point.pk,
            "by": EmployeeFactory(organization=self.admin_user.organization).pk,
            "remarks": self.fake.text(128),
            "transport": random.randint(10, 15),
            "transfer_status": random.choice(TransferStatusType.get_values()),
            "stock_io_logs": [
                {
                    # Stock IO Log for stock in
                    "stock": stock_in.pk,
                    "quantity": random.randint(1, 100),
                    "batch": 'batch-123',
                    "expire_date": str(self.fake.date())
                }
            ],
            "received_by": EmployeeFactory(organization=self.admin_user.organization).pk
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
        request = self.client.post(
            self.url,
            data=json.dumps(dict(data)),
            content_type='application/json'
        )

        self.assertCreated(request)
        self.assertEqual(request.data['date'], data['date'])
        self.assertEqual(request.data['transfer_from'], data['transfer_from'])
        self.assertEqual(request.data['transfer_to'], data['transfer_to'])
        self.assertEqual(request.data['remarks'], data['remarks'])
        self.assertEqual(request.data['by'], data['by'])
        self.assertEqual(request.data['transport'], data['transport'])
        self.assertEqual(request.data['received_by'], data['received_by'])
        self.assertEqual(request.data['transfer_status'], data['transfer_status'])    
        # Stock IO Log Test
        self.assertEqual(StockTransfer.objects.count(), 1)
        self.assertEqual(StockIOLog.objects.count(), 2)

        # ===========================================
        #  Check transaction for stock transfer
        # ===========================================

        # refresh stock from database
        stock_in.refresh_from_db()
        stock_out.refresh_from_db()
        # need a stock quantity from stock io logs
        stock_transfer_in = data['stock_io_logs'][0]['quantity']
        # check equality for stock in
        self.assertNotEqual(stock_in_before - stock_transfer_in, stock_in.stock)
        # check equality for stock out
        self.assertNotEqual(stock_out_before + stock_transfer_in, stock_out.stock)

        # admin user logout
        self.client.logout()