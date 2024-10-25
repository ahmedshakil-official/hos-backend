from django.urls import reverse

from common.test_case import OmisTestCase

from pharmacy.tests import EmployeeAccountAccessFactory
from core.tests import EmployeeFactory

class EmployeeAccountListAPITest(OmisTestCase):

    def setUp(self):
        super(EmployeeAccountListAPITest, self).setUp()
        self.employee = EmployeeFactory(organization=self.admin_user.organization)
        self.url = reverse('pharmacy.employee-account.list', args=[self.employee.alias])

    def test_employee_account_list_get(self):
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
        employee_account = EmployeeAccountAccessFactory(
            organization=self.admin_user.organization,
            employee=self.employee,
            access_status=True
        )

        request = self.client.get(self.url)
        self.assertSuccess(request)
        # check if it is the same user
        self.assertEqual(request.data['count'], 1)
        self.assertEqual(request.data['results'][0]['account']['id'],
                         employee_account.account.id)
        self.assertEqual(request.data['results'][0]['account']['alias'],
                         str(employee_account.account.alias))
        self.assertEqual(request.data['results'][0]['employee']['id'],
                         employee_account.employee.id)
        self.assertEqual(request.data['results'][0]['employee']['alias'],
                         str(employee_account.employee.alias))

        # admin user logout
        self.client.logout()
