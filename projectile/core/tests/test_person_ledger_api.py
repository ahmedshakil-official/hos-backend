from django.urls import reverse
from common.test_case import OmisTestCase
from common.enums import Status
from account.tests import TransactionFactory
from clinic.tests import ServiceConsumedFactory
from pharmacy.tests import SalesFactory
from . import PersonOrganizationFactory


class PatientLedgerAPITest(OmisTestCase):

    def setUp(self):
        super(PatientLedgerAPITest, self).setUp()

        #Create a patient instance
        self.patient_organization = PersonOrganizationFactory(
            organization=self.admin_user.organization,
        )

        #create a transaction for the patient
        self.transaction = TransactionFactory(
            organization=self.admin_user.organization,
            status=Status.ACTIVE,
            person_organization=self.patient_organization,
            paid_by=self.patient_organization.person
        )

        #create a service consumed for patient
        self.service_consumed = ServiceConsumedFactory(
            organization=self.admin_user.organization,
            status=Status.ACTIVE,
            person_organization_patient=self.patient_organization,
            person=self.patient_organization.person
        )

        #create a service consumed for patient
        self.sales = SalesFactory(
            organization=self.admin_user.organization,
            status=Status.ACTIVE,
            person_organization_buyer=self.patient_organization,
            buyer=self.patient_organization.person
        )

        self.url = reverse('person-ledger', args=[self.patient_organization.alias])


    def test_patient_ledger_get(self):
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
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same instance
        # self.assertEqual(request.data['id'], self.patient_organization.pk)
        # self.assertEqual(request.data['person']['alias'], str(self.patient_organization.person.alias))

        # check if it is the same transaction instance
        self.assertEqual(request.data['transaction'][0]['alias'], str(self.transaction.alias))
        self.assertEqual(request.data['transaction'][0]['amount'], int(self.transaction.amount))

        # check if it is the same sales instance
        self.assertEqual(request.data['sales'][0]['alias'], str(self.sales.alias))
        self.assertEqual(request.data['sales'][0]['amount'], float(self.sales.amount))

        # logout
        self.client.logout()
