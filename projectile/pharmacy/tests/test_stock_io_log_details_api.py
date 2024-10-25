import json
import random
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status

from ..tests import StockFactory, ProductFactory, StockIOLogFactory, PurchaseFactory
from ..enums import StockIOType

class StockIOLogDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(StockIOLogDetailsAPITest, self).setUp()

        # set a product
        self.stock = StockFactory(
            product=ProductFactory(organization=self.admin_user.organization),
            organization=self.admin_user.organization
        )
        self.stock_io_log = StockIOLogFactory(
            stock=self.stock,
            organization=self.admin_user.organization
        )

        # set the url
        self.url = reverse('pharmacy.stock-io-log-details', args=[self.stock_io_log.alias])

    def test_stock_io_log_details_get(self):
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

        # Check if it is the same data
        self.assertEqual(request.data['id'], self.stock_io_log.id)
        self.assertEqual(request.data['quantity'], self.stock_io_log.quantity)
        self.assertEqual(request.data['alias'], str(self.stock_io_log.alias))

        # admin user logout
        self.client.logout()

    def test_stock_io_log_details_put(self):

        data = {
            'quantity': random.randint(1, 5),
            'rate': random.randint(10, 15),
            'batch': self.fake.first_name(),
            'expire_date': self.fake.date(),
            'date': self.fake.date(),
            'type': StockIOType.INPUT,
            'purchase': PurchaseFactory().pk,
            'stock': StockFactory().pk
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
        request = self.client.put(self.url,
                                  data=json.dumps(dict(data)), content_type='application/json'
                                 )
        self.assertSuccess(request)

        # Check if is the same data
        self.assertEqual(request.data['quantity'], data['quantity'])
        self.assertEqual(request.data['rate'], data['rate'])
        self.assertEqual(request.data['batch'], data['batch'].upper())

        # admin user logout
        self.client.logout()

    def test_stock_io_log_details_patch(self):

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
        request = self.client.patch(self.url,
                                    data=json.dumps(dict(data)), content_type='application/json'
                                   )
        self.assertSuccess(request)

        # Check if is the same data
        self.assertEqual(request.data['status'], data['status'])

        # admin user logout
        self.client.logout()
