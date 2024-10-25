from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status
from account.enums import TransactionHeadGroup
from account.tests import AccountFactory, TransactionHeadFactory


class AccountTransactionHeadSearchAPITest(OmisTestCase):
    url = reverse('accounts.transaction-search')

    # def setUp(self):
    #     super(AccountTransactionHeadSearchAPITest, self).setUp()

    def test_account_search_get(self):
        transaction_head = TransactionHeadFactory(
            organization=self.admin_user.organization,
            status=Status.ACTIVE,
            name='Text',
            group=TransactionHeadGroup.EMPLOYEE
        )

        # search data
        data1 = {
            'keyword': 'search'
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
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 0)
        self.assertSuccess(request)

        # check with another keywod
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()
