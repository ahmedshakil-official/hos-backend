from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status
from core.tests import PersonOrganizationGroupPermissionFactory
from account.tests import AccountFactory


class AccountSearchAPITest(OmisTestCase):
    url = reverse('accounts-search')

    # def setUp(self):
    #     super(AccountSearchAPITest, self).setUp()

    def test_account_search_get(self):
        PersonOrganizationGroupPermissionFactory(
            person_organization=self.person_organization_employee,
            permission=self.admin_group
        )
        account = AccountFactory(
            organization=self.employee_user.organization,
            status=Status.ACTIVE,
            name='test',
            description='text'
        )

        # search data
        data1 = {
            'keyword': 'test'
        }

        data2 = {
            'keyword': 'text'
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
        self.client.logout()

        # ===========================================
        #  Check for acocunts employee user
        # ===========================================
        login = self.client.login(
            phone=self.person_organization_employee.phone,
            password='testpass'
        )
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.employee_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)
        self.assertEqual(
            request.data['results'][0]['name'], account.name
        )
        self.assertEqual(
            request.data['results'][0]['description'], account.description
        )

        # check with another keywod
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 0)

        # logout
        self.client.logout()
