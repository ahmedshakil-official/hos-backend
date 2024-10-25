from django.urls import reverse
from common.test_case import OmisTestCase
from pharmacy.tests import PurchaseFactory
from core.tests import PersonOrganizationSupplierFactory
from pharmacy.enums import PurchaseType, PurchaseOrderStatus
from common.enums import Status


class PurchaseOrderPendingSearchAPITest(OmisTestCase):
    url = reverse('pharmacy.product.purchase_order_pending_search')

    # def setUp(self):
    #     super(PurchaseOrderPendingSearchAPITest, self).setUp()

    def test_purchase_order_pending_search_get(self):
        supplier = PersonOrganizationSupplierFactory(
            company_name='test',
            organization=self.admin_user.organization
        )

        purchase_order_pending = PurchaseFactory.create_batch(
            3,
            organization=self.admin_user.organization,
            purchase_type=PurchaseType.ORDER,
            purchase_order_status=PurchaseOrderStatus.PENDING,
            person_organization_supplier=supplier,
            status=Status.PURCHASE_ORDER
        )

        # search keywords
        data1 = {
            'keyword': 'best'
        }

        data2 = {
            'keyword': 'test'
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
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check if data1 keyword returns zero search result
        self.assertEqual(request.data['count'], 0)

        # check with data2 keyword
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if data2 keyword returns three search result
        self.assertEqual(request.data['count'], 3)

        # delete first entry
        purchase_order_pending[0].delete()

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if it is now returns two result after deletion
        self.assertEqual(request.data['count'], 2)

        # logout
        self.client.logout()
