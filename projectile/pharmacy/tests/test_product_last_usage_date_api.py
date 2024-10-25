import random
import datetime
from django.urls import reverse
from django.utils import timezone
from common.enums import Status
from common.test_case import OmisTestCase
from ..tests import StockIOLogFactory, StorePointFactory, ProductFactory, StockFactory
from ..models import StockIOLog

def generate_date():
    date_time = datetime.datetime.strptime(
        '{} {}'.format(random.randint(1, 366), 2019), '%j %Y'
    )
    return str(timezone.make_aware(
        date_time,
        timezone.get_current_timezone()
    ).date())

def get_latest_io_log(organization, stock, batch):
    stock_io_logs = []
    for item in range(3):
        stock_io_logs.append(
            StockIOLogFactory(
                organization=organization,
                stock=stock,
                batch=batch,
                date=generate_date(),
            )
        )
    stock_io_logs.sort(
        key=lambda item: datetime.datetime.strptime(item.date, '%Y-%m-%d'))
    return stock_io_logs[-1]


class ProductLastUsageDate(OmisTestCase):
    url = reverse('pharmacy.product-last-usage')

    def test_product_last_usage_date(self):
        # Create Product
        product = ProductFactory(
            organization=self.admin_user.organization,
        )
        store_points = StorePointFactory.create_batch(
            2, organization=self.admin_user.organization
        )
        stocks = []
        for store in store_points:
            stocks.append(
                StockFactory(
                    product=product,
                    store_point=store,
                    organization=self.admin_user.organization,
                    status=Status.ACTIVE,
                )
            )

        # get latest stock_io_logs based on date
        latest_io_log_1 = get_latest_io_log(
            self.admin_user.organization, stocks[0], 'AAA')
        latest_io_log_2 = get_latest_io_log(
            self.admin_user.organization, stocks[1], 'CCC')

        params = [
            {
                'stocks': stocks[0].alias,
                'batch': 'AAA'
            },
            {
                'stocks': stocks[1].alias,
                'batch': 'CCC'
            },
        ]
        stock_1 = StockIOLog.objects.filter(
            stock__alias=stocks[0].alias, batch='AAA', status=Status.ACTIVE).values('stock')
        stock_2 = StockIOLog.objects.filter(
            stock__alias=stocks[1].alias, batch='CCC', status=Status.ACTIVE).values('stock')
                #=============================================
        # Check without login
        #=============================================
        request = self.client.get(self.url, params[0])
        self.assertPermissionDenied(request)

        #=============================================
        # Check with login
        #=============================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, params[0])
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ============================================
        # Check for admin user
        # ============================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)

        #===================================================
        # fetch successfully
        # ==================================================
        self.assertSuccess(request)
        request = self.client.get(self.url, params[0])
        self.assertSuccess(request)
        # check last usage date with first created stock
        self.assertEqual(request.data[0]['batch'], latest_io_log_1.batch)
        self.assertEqual(request.data[0]['last_usage'], latest_io_log_1.date)
        self.assertEqual(request.data[0]['stock'], stock_1[0]['stock'])
        request = self.client.get(self.url, params[1])
        self.assertSuccess(request)
        # check last usage date with secondly created stock
        self.assertEqual(request.data[0]['batch'], latest_io_log_2.batch)
        self.assertEqual(request.data[0]['last_usage'], latest_io_log_2.date)
        self.assertEqual(request.data[0]['stock'], stock_2[0]['stock'])
        self.client.logout()
