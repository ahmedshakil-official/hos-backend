from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status

from core.tests import EmployeeFactory

from pharmacy.tests import StockTransferFactory, StorePointFactory


class StockTransferSearchAPITest(OmisTestCase):
    url = reverse('pharmacy.product.stock.transfer-search')
    fake = Faker()

    # def setUp(self):
    #     super(StockTransferSearchAPITest, self).setUp()

    def test_stock_transfer_search_get(self):
        # first create some persons
        stock_transfer_from = StorePointFactory(
            name='myy', organization=self.admin_user.organization)
        stock_transfer_to = StorePointFactory(
            name='myyne', organization=self.admin_user.organization)
        stock_received_by = EmployeeFactory(
            first_name='fname', organization=self.admin_user.organization)
        stock_transfers = StockTransferFactory.create_batch(
            2,
            organization=self.admin_user.organization,
            transfer_from=stock_transfer_from,
            transfer_to=stock_transfer_to,
            received_by=stock_received_by,
            person_organization_by=stock_received_by.person_organization.first(),
            status=Status.ACTIVE
        )

        # search data
        data1 = {
            'keyword': 'cyy'
        }

        data2 = {
            'keyword': 'myy'
        }

        data3 = {
            'keyword': 'fname'
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

         # check with another keywod
        request = self.client.get(self.url, data3)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 2)

        # delete first entry
        stock_transfers[0].delete()

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        request = self.client.get(self.url, data3)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()
