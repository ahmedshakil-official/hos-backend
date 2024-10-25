import json
import random
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase

from ..tests import StockFactory
from ..models import StockIOLog, Stock
from ..enums import StockIOType
from common.enums import Status


class StockIOLogBatchUpdateAPITest(OmisTestCase):
    url = reverse('pharmacy.stock-io-log-bulk-create')
    fake = Faker()

    def setUp(self):
        super(StockIOLogBatchUpdateAPITest, self).setUp()

    def test_stock_io_log_batch_update_post(self):
        stock_id = StockFactory(organization=self.admin_user.organization)
        stock_number = stock_id.stock
        data = {
            'stock_io_logs': [
                {
                    'status': Status.ACTIVE,
                    'expire_date': str(self.fake.date()),
                    'batch': self.fake.text(128),
                    'rate': stock_id.product.purchase_price,
                    'type': StockIOType.INPUT,
                    'stock': stock_id.pk,
                    'quantity': random.randint(5, 8),
                },
                {
                    'status': Status.ACTIVE,
                    'expire_date': str(self.fake.date()),
                    'batch': self.fake.text(128),
                    'rate': stock_id.product.purchase_price,
                    'type': StockIOType.INPUT,
                    'stock': stock_id.pk,
                    'quantity': random.randint(5, 8),
                }
            ]
        }
        # with same batch from first data and type out
        data2 = {
            'stock_io_logs': [
                {
                    'status': Status.ACTIVE,
                    'expire_date': str(self.fake.date()),
                    'batch': data['stock_io_logs'][0]['batch'],
                    'rate': stock_id.product.purchase_price,
                    'type': StockIOType.OUT,
                    'stock': stock_id.pk,
                    'quantity': random.randint(1, 4),
                }
            ]
        }
        # different batch and type out
        data3 = {
            'stock_io_logs': [
                {
                    'status': Status.ACTIVE,
                    'expire_date': str(self.fake.date()),
                    'batch': self.fake.text(128),
                    'rate': stock_id.product.purchase_price,
                    'type': StockIOType.OUT,
                    'stock': stock_id.pk,
                    'quantity': random.randint(1, 3),
                }
            ]
        }

        # ===========================================
        #  Check without login
        # ===========================================
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
        request = self.client.post(self.url, data=json.dumps(dict(data)), content_type='application/json')
        self.assertCreated(request)

        # check stock
        self.assertEqual(Stock.objects.count(), 1)

        # After created check with stockio count
        self.assertEqual(StockIOLog.objects.count(), 2)

        # Again request with data2
        request = self.client.post(
            self.url, data=json.dumps(dict(data2)),
            content_type='application/json'
        )
        self.assertCreated(request)

        # After created another stockio chech with count
        self.assertEqual(StockIOLog.objects.count(), 3)

        # subtract stockio in and stockio out
        stock_rest = data['stock_io_logs'][0]['quantity'] + data['stock_io_logs'][1]['quantity'] - data2['stock_io_logs'][0]['quantity']

        # After out a product from stockio check stock are equal or not
        self.assertEqual(Stock.objects.get(pk=stock_id.pk).stock, stock_number + stock_rest)

        # If in and out batch is not same then request will rejected
        if data['stock_io_logs'][0]['batch'] != data3['stock_io_logs'][0]['batch'] \
                and data['stock_io_logs'][1]['batch'] != data3['stock_io_logs'][0]['batch']:
            request = self.client.post(
                self.url, data=json.dumps(dict(data3)),
                content_type='application/json'
            )
            self.assertBadRequest(request)

            # Check stockio remain same after bad request
            self.assertEqual(StockIOLog.objects.count(), 3)

        # admin user logout
        self.client.logout()
