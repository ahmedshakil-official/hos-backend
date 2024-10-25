from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status

from core.tests import PatientFactory, PersonOrganizationGroupPermissionFactory

from account.tests import TransactionFactory


class TransactionSearchAPITest(OmisTestCase):
    url = reverse('accounts-transaction')

    def setUp(self):
        super(TransactionSearchAPITest, self).setUp()
        PersonOrganizationGroupPermissionFactory(
            person_organization=self.person_organization_employee,
            permission=self.admin_group
        )
        patient = PatientFactory(first_name='test', organization=self.employee_user.organization)
        person_organization_patient = patient.person_organization.get(
            organization=self.employee_user.organization,
            person_group=patient.person_group
        )
        # account = AccountFactory(organization=self.admin_user.organization)
        self.transaction = TransactionFactory.create_batch(
            3, paid_by=patient,
            person_organization=person_organization_patient,
            organization=self.employee_user.organization,
            status=Status.ACTIVE
        )

    def test_transaction_search_get(self):

        data1 = {
            'keyword': 'nest'
        }

        data2 = {
            'keyword': 'test'
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
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.employee_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check if data1 keyword returns zero search result
        self.assertEqual(request.data['count'], 0)

        # check with data2 keyword
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if data2 keyword returns three search result
        self.assertEqual(request.data['count'], 3)

        # delete first entry
        self.transaction[0].delete()

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if it is now returns two result after deletion
        self.assertEqual(request.data['count'], 2)

        # logout
        self.client.logout()
