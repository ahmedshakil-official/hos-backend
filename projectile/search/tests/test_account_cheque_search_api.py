from django.urls import reverse

from common.test_case import OmisTestCase
from account.tests import AccountFactory, AccountChequeFactory


class AccountChequeSearchAPITest(OmisTestCase):
    url = reverse('account-cheque-search')

    # def setUp(self):
    #     super(AccountChequeSearchAPITest, self).setUp()

    def test_account_cheque_search_get(self):
        account = AccountFactory(name='TEST')
        account_cheque = AccountChequeFactory.create_batch(
            2,
            organization=self.admin_user.organization,
            account=account
            )

        # search data
        data1 = {
            'keyword': 'les'
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


        # check with another keywod
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 2)

        # logout
        self.client.logout()
