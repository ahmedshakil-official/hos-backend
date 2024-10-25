from django.urls import reverse

from common.test_case import OmisTestCase
from account.enums import AccountType
from account.tests import AccountFactory
from pharmacy.models import EmployeeAccountAccess
from core.enums import PersonGroupType
from core.tests import (
    EmployeeFactory,
    PersonFactory,
    GroupPermissionFactory,
    PersonOrganizationGroupPermissionFactory
)


class CashAccountSearchAPITest(OmisTestCase):
    url = reverse('cash-accounts-search')

    # def setUp(self):
    #     super(CashAccountSearchAPITest, self).setUp()

    def test_cash_account_search_get(self):

        employee_user = PersonFactory(
            is_staff=True,
            person_group=PersonGroupType.EMPLOYEE
        )

        person_organization_employee = employee_user.get_person_organization_for_employee()

        employee_group_permission = PersonOrganizationGroupPermissionFactory(
            person_organization=person_organization_employee,
            permission=self.accounts_group
        )

        account = AccountFactory(
            organization=self.admin_user.organization,
            name='test',
            type=AccountType.CASH
        )

        employee_cash_account = AccountFactory(
            name='test',
            organization=employee_user.organization,
            type=AccountType.CASH
        )

        employee_account_access = EmployeeAccountAccess.objects.get(employee=employee_user)
        employee_account_access.access_status = True
        employee_account_access.save()

        data1 = {
            'keyword': 'test'
        }

        data2 = {
            'keyword': 'testtest'
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.employee_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # ===========================================
        #  Check for acocunts employee user
        # ===========================================
        login = self.client.login(
            phone=person_organization_employee.phone,
            password='testpass'
        )
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)
        self.assertEqual(request.data['count'], 1)

        self.assertEqual(
            request.data['results'][0]['name'], employee_account_access.account.name
        )
        self.assertEqual(
            request.data['results'][0]['id'], employee_account_access.account.id
        )

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)
        self.assertEqual(request.data['count'], 0)

        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=employee_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)


        # check with another keyword
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 0)

        # logout
        self.client.logout()
