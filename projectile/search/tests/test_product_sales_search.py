from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from core.tests import PersonFactory, EmployeeFactory, PatientFactory, PersonOrganizationFactory

from pharmacy.tests import SalesFactory, StockFactory


class ProductSalesSearchAPITest(OmisTestCase):
    url = reverse('pharmacy.product.sales.search')
    fake = Faker()

    # def setUp(self):
    #     super(ProductSalesSearchAPITest, self).setUp()

    def test_product_medicine_list_get(self):
        # first create some persons
        buyer1_will_be_deleted = PersonFactory(first_name='TEST')
        buyer = PersonOrganizationFactory(
            person=buyer1_will_be_deleted,
            first_name="test")
        sales_will_be_deleted = SalesFactory.create_batch(
            2,
            organization=self.admin_user.organization,
            buyer=buyer1_will_be_deleted, person_organization_buyer=buyer)
        # search data
        data1 = {
            'keyword': 'ct'
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
        sales_will_be_deleted[0].delete()

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()
