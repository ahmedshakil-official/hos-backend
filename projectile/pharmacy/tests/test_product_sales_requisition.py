from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status

from ..tests import SalesFactory
from ..models import Sales


class ProductSalesRequisitionListAPITest(OmisTestCase):
    url = reverse('pharmacy.product.sales.requisition-list')

    def setUp(self):
        super(ProductSalesRequisitionListAPITest, self).setUp()

    def test_sales_requisition_list_get(self):
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

        sales_will_be_deleted = SalesFactory.create_batch(
            5, organization=self.admin_user.organization)
        requisitions = [item for item in sales_will_be_deleted
                        if item.status == Status.DRAFT]

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], len(requisitions))

        sales_will_be_deleted[0].delete()
        requisitions = Sales.objects.filter(status=Status.DRAFT)

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], len(requisitions))

        # admin user logout
        self.client.logout()
