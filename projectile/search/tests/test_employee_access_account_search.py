from django.urls import reverse

from common.test_case import OmisTestCase
from core.tests import EmployeeFactory
from pharmacy.tests import EmployeeAccountAccessFactory
from account.tests import AccountFactory


class EmployeeAccessAccountSearchAPITest(OmisTestCase):

    def setUp(self):
        super(EmployeeAccessAccountSearchAPITest, self).setUp()
        #first creat an employee and and an account
        self.employee = EmployeeFactory(organization=self.admin_user.organization)
        self.account = AccountFactory(
            name='test',
            organization=self.admin_user.organization
        )
        # Create access for the employee to account
        self.employee_account = EmployeeAccountAccessFactory(
            organization=self.admin_user.organization,
            employee=self.employee,
            access_status=True,
            account=self.account
        )
        self.url = reverse('employee-access-accounts-search', args=[self.employee.alias])

    def test_employee_access_account_search_get(self):

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
        self.assertEqual(request.data, [])


        # check with another keywod
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data[0]['id'], self.account.id)
        self.assertEqual(request.data[0]['alias'], str(self.account.alias))
        self.assertEqual(request.data[0]['balance'], self.account.balance)

        # logout
        self.client.logout()
