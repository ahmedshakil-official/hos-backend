from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status

from core.tests import PatientFactory, SupplierFactory


class PatientSupplierSearchAPITest(OmisTestCase):
    url = reverse('patient-supplier-search')

    # def setUp(self):
    #     super(PatientSupplierSearchAPITest, self).setUp()

    def test_patient_supplier_search_get(self):
        # first create patient and supplier
        patient = PatientFactory(
            first_name="test",
            organization=self.admin_user.organization,
            status=Status.ACTIVE
        )
        supplier = SupplierFactory(
            company_name="test Store",
            organization=self.admin_user.organization,
            status=Status.ACTIVE
        )

        # search data
        data = {
            'keyword': 'test'
        }

        data_2 = {
            'keyword': 'store'
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.get(self.url, data)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 2)

        # Check if request company name and supplier are same
        self.assertEqual(request.data['results'][0]['company_name'], supplier.company_name)

        # test with keyword that return none
        request = self.client.get(self.url, data_2)
        self.assertSuccess(request)

        # check is it return 0 data
        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()
