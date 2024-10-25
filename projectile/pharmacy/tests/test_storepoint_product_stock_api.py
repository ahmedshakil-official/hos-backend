from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status

from ..tests import StorePointFactory, PurchaseFactory, StockIOLogFactory, StockFactory
from ..enums import PurchaseType


class OrderedProductStockListAPITest(OmisTestCase):

    def setUp(self):
        super(OrderedProductStockListAPITest, self).setUp()

        self.store_point = StorePointFactory(organization=self.admin_user.organization)
        self.stock = StockFactory(
            organization=self.admin_user.organization,
            store_point=self.store_point,
        )
        self.purchase_order = PurchaseFactory(
            organization=self.admin_user.organization,
            status=Status.PURCHASE_ORDER,
            purchase_type=PurchaseType.ORDER,
            is_sales_return=False
            )

        self.stock_io_logs = StockIOLogFactory(
            organization=self.admin_user.organization,
            status=Status.PURCHASE_ORDER,
            purchase=self.purchase_order,
            stock=self.stock
            )

        self.url = reverse('pharmacy.ordered-product-stock',
                           args=[self.store_point.alias, self.purchase_order.alias])

    def test_ordered_product_stock_list_get(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)
        self.assertEqual(request.data['count'], 1)
        self.assertEqual(request.data['results'][0]['product'], self.stock.product.id)
        self.client.logout()
