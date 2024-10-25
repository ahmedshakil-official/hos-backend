from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from ..tests import StockAdjustmentFactory


class StockDisbursementListApiTest(OmisTestCase):
    url = reverse('pharmacy.stock-disbursements')
    fake = Faker()

    def setUp(self):
        super(StockDisbursementListApiTest, self).setUp()

    def test_stock_adjustment_list_get(self):
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

        stock_disbursement = StockAdjustmentFactory.create_batch(
            2,
            organization=self.admin_user.organization,
            is_product_disbrustment=True
        )

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        stock_disbursement[0].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)
        self.assertEqual(request.data['results'][0]['id'], stock_disbursement[1].id)
        self.assertEqual(request.data['results'][0]['alias'], str(stock_disbursement[1].alias))
        self.assertEqual(
            request.data['results'][0]['store_point']['id'],
            stock_disbursement[1].store_point.id)
        self.assertEqual(
            request.data['results'][0]['store_point']['alias'],
            str(stock_disbursement[1].store_point.alias))
        self.assertEqual(
            request.data['results'][0]['person_organization_employee']['id'],
            stock_disbursement[1].person_organization_employee.id)
        self.assertEqual(
            request.data['results'][0]['person_organization_employee']['alias'],
            str(stock_disbursement[1].person_organization_employee.alias))
        self.assertEqual(
            request.data['results'][0]['person_organization_patient']['id'],
            stock_disbursement[1].person_organization_patient.id)
        self.assertEqual(
            request.data['results'][0]['person_organization_patient']['alias'],
            str(stock_disbursement[1].person_organization_patient.alias))
        # admin user logout
        self.client.logout()
