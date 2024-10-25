import random
from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status

from ..tests import (
    StorePointFactory,
    StockIOLogFactory,
    StockFactory,
    PurchaseFactory
)

from ..models import StockIOLog
from ..enums import PurchaseType


class TestLatestDiscountVatAPI(OmisTestCase):
    def setUp(self):
        super(TestLatestDiscountVatAPI, self).setUp()

        self.store = StorePointFactory(organization=self.admin_user.organization)
        self.purchase = PurchaseFactory(
            organization=self.admin_user.organization,
            is_sales_return=False,
            status=Status.ACTIVE,
            purchase_type=PurchaseType.PURCHASE
        )
        self.vat_rate = random.randint(1, 10)
        self.discount_rate = random.randint(1, 10)
        StockIOLogFactory.create_batch(
            random.randint(1, 20),
            organization=self.admin_user.organization,
            purchase=self.purchase,
            vat_rate=self.vat_rate,
            discount_rate=self.discount_rate,
            stock=StockFactory(
                organization=self.admin_user.organization, store_point=self.store
            )
        )

    def test_purchase_post_for_latest_discount_vat(self):
        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        # Set up url
        stock_alias = StockIOLog.objects.all()[0].stock.alias
        url = reverse('stocks-lastest-vat-discount', args=[stock_alias])

        params = {
            'is_purchase': 'true',
            'is_order': '',
            'is_sales': '',
        }
        request = self.client.get(url, params)
        self.assertSuccess(request)
        self.assertEqual(float(self.vat_rate), float(request.data['vat_rate']))
        self.assertEqual(float(self.discount_rate), float(request.data['discount_rate']))

        # admin user logout
        self.client.logout()
