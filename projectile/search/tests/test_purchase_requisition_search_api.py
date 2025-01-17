import random

from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status
from pharmacy.tests import PurchaseFactory, StorePointFactory
from pharmacy.enums import PurchaseOrderStatus, PurchaseType

class PurchaseRequisitionSearchAPITest(OmisTestCase):
    url = reverse('pharmacy.product.purchase_requisition_search')

    # def setUp(self):
    #     super(PurchaseRequisitionSearchAPITest, self).setUp()

    def test_purchase_requisition_search_get(self):
        
        store_point = StorePointFactory(
            organization=self.admin_user.organization,
            status=Status.ACTIVE,
            name='TEST'
        )
        purchase_requisition = PurchaseFactory.create_batch(
            2,
            organization=self.admin_user.organization,
            purchase_type=PurchaseType.REQUISITION,
            purchase_order_status=PurchaseOrderStatus.DEFAULT,
            status=Status.DRAFT,
            amount=random.randint(500, 1000),
            store_point=store_point
        )

        # search data
        data1 = {
            'keyword': 'mes'
        }

        data2 = {
            'keyword': 'tes'
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 0)


        # check with another keywod
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 2)

        # delete first entry
        purchase_requisition[0].delete()

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()
