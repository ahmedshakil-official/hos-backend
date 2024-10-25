import random
from faker import Faker
from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status
from ..enums import PurchaseOrderStatus, PurchaseType

from ..tests import PurchaseFactory, StorePointFactory


class PurchaseOrderCompletedListAPITest(OmisTestCase):
    url = reverse('pharmacy.purchase-purchase-order-completed')
    fake = Faker()

    def setUp(self):
        super(PurchaseOrderCompletedListAPITest, self).setUp()

    def test_purchase_order_completed_list_get(self):
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

        storepoint = StorePointFactory(
            organization=self.admin_user.organization,
            status=Status.ACTIVE,
            name=self.fake.first_name()
        )
        purchase_order_completed = PurchaseFactory(
            organization=self.admin_user.organization,
            purchase_type=PurchaseType.ORDER,
            purchase_order_status=PurchaseOrderStatus.COMPLETED,
            status=Status.PURCHASE_ORDER,
            amount=random.randint(500, 1000),
            store_point=storepoint,
            is_sales_return=False
        )

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # # check if it is the same user
        self.assertEqual(float(purchase_order_completed.amount),
                         request.data['results'][0]['amount'])
        self.assertEqual(str(purchase_order_completed.alias),
                         request.data['results'][0]['alias'])

        # # admin user logout
        self.client.logout()
