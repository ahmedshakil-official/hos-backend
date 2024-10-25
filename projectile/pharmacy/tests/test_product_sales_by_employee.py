
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from core.tests import PersonFactory, EmployeeFactory, PatientFactory



class ProductSalesByEmployeeAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(ProductSalesByEmployeeAPITest,self).setUp()
    
    def testProductSaleByEmployee(self):
        self.employee = EmployeeFactory(organization=self.admin_user.organization)
        self.url = reverse('pharmacy.product.sales-by-employee',
                           args=[self.employee.alias])

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

        # calling the api
        request = self.client.get(self.url)
        self.assertSuccess(request)
        length = len(request.data)

        self.client.logout()