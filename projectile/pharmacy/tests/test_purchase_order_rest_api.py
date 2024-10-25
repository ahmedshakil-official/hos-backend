import random
from faker import Faker
from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status
from ..enums import PurchaseOrderStatus, PurchaseType

from ..tests import PurchaseFactory, StorePointFactory, StockFactory, StockIOLogFactory


class PurchaseOrderRestListAPITest(OmisTestCase):

    fake = Faker()

    def setUp(self):
        super(PurchaseOrderRestListAPITest, self).setUp()

        self.storepoint = StorePointFactory(
            organization=self.admin_user.organization,
            status=Status.ACTIVE,
            name=self.fake.first_name()
        )
        self.purchase_order = PurchaseFactory(
            organization=self.admin_user.organization,
            purchase_type=PurchaseType.ORDER,
            purchase_order_status=PurchaseOrderStatus.PENDING,
            status=Status.PURCHASE_ORDER,
            amount=random.randint(10, 20),
            store_point=self.storepoint,
            is_sales_return=False
        )
        order_stock = StockFactory(organization=self.admin_user.organization)
        order_stock_io_log = StockIOLogFactory(
            status=self.purchase_order.status,
            organization=self.admin_user.organization,
            stock=order_stock,
            purchase=self.purchase_order,
            quantity=random.randint(20, 30),
        )
        self.ordered_quantity = order_stock_io_log.quantity
        self.purchase = PurchaseFactory(
            organization=self.admin_user.organization,
            purchase_type=PurchaseType.PURCHASE,
            status=Status.ACTIVE,
            amount=random.randint(5, 10),
            store_point=self.storepoint,
            is_sales_return=False,
            copied_from=self.purchase_order
        )
        purchase_stock_io_log = StockIOLogFactory(
            status=self.purchase.status,
            organization=self.admin_user.organization,
            stock=order_stock,
            purchase=self.purchase,
            quantity=random.randint(10, 15),
            primary_unit=order_stock_io_log.primary_unit,
            rate=order_stock_io_log.rate,
        )
        self.purchase_quantity = purchase_stock_io_log.quantity
        self.url = reverse('pharmacy.purchase-order-rest',
                           args=[self.purchase_order.alias])

    def test_purchase_order_rest_list_get(self):
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
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        rest_item = self.ordered_quantity - self.purchase_quantity
        self.assertEqual(rest_item,
                         request.data[0]['rest_item'])

        # # admin user logout
        self.client.logout()
