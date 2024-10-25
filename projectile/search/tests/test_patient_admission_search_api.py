from django.urls import reverse
from common.test_case import OmisTestCase
from core.tests import PatientFactory, PersonOrganizationPatientFactory
from clinic.tests import PatientAdmissionFactory, PersonOrganizationPatientAdmissionFactory


class PatientAdmissionSearchAPITest(OmisTestCase):
    url = reverse('patient-admission-search')

    # def setUp(self):
    #     super(PatientAdmissionSearchAPITest, self).setUp()

    def test_patient_admission_search_get(self):
        # first create some persons
        patient = PatientFactory(first_name='TEST', last_name='TEST')
        person_organization_patient = PersonOrganizationPatientFactory(first_name='TEST', last_name='TEST')
        patient_admission = PersonOrganizationPatientAdmissionFactory.create_batch(
            2,
            organization=self.admin_user.organization,
            patient=patient,
            person_organization_patient=person_organization_patient,
        )

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

        # check if it is the same instance
        self.assertEqual(request.data['count'], 2)

        # delete first entry
        patient_admission[0].delete()

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)
        self.assertEqual(
            request.data['results'][0]['person_organization_patient']['alias'],
            str(patient_admission[0].person_organization_patient.alias)
        )

        # logout
        self.client.logout()
