import random

from django.urls import reverse

from common.test_case import OmisTestCase
from clinic.tests import AppointmentTreatmentSessionFactory
from prescription.tests import PrescriptionFactory
from . import PatientFactory
from ..models import PersonOrganization

class PrescriptionHistroyAPITest(OmisTestCase):

    def setUp(self):
        super(PrescriptionHistroyAPITest, self).setUp()
        # create a designation
        self.patient = PatientFactory(organization=self.admin_user.organization)
        self.person_organization = PersonOrganization.objects.get(person=self.patient)
        self.prescription_count = random.randint(1, 10)
        self.appointment_count = random.randint(1, 5)

        PrescriptionFactory.create_batch(
            self.prescription_count, organization=self.admin_user.organization,
            patient=self.patient,
            person_organization_patient=self.person_organization
        )
        AppointmentTreatmentSessionFactory.create_batch(
            self.appointment_count, organization=self.admin_user.organization,
            person=self.patient,
            person_organization=self.person_organization
        )

        self.url = reverse('prescription-history', args=[self.person_organization.alias])

    def test_patient_meta_data_details_get(self):
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

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)
        # check if it is the same instance
        self.assertEqual(request.data['results'][0]['patient']['id'], self.patient.pk)
        self.assertEqual(request.data['results'][0]['patient']['alias'], str(self.patient.alias))
        self.assertEqual(
            request.data['count'], self.prescription_count)

        # logout
        self.client.logout()
