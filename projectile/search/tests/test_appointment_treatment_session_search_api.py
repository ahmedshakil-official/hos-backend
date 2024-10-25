from django.urls import reverse
from common.test_case import OmisTestCase
from common.enums import Status
from core.tests import PersonOrganizationFactory
from clinic.tests import AppointmentTreatmentSessionFactory
from clinic.enums import AppointmentType, AppointmentKind


class AppointmentTreatmentSessionSearchAPITest(OmisTestCase):
    url = reverse("appointment-treatment-session-search")

    # def setUp(self):
    #     super(AppointmentTreatmentSessionSearchAPITest, self).setUp()

    def test_appointment_treatment_session_search_get(self):
        person_organization = PersonOrganizationFactory(
            first_name='test',
            organization=self.admin_user.organization
        )
        appointment_session = AppointmentTreatmentSessionFactory.create_batch(
            10,
            person_organization=person_organization,
            organization=self.admin_user.organization,
            type=AppointmentType.CONFIRMED,
            kind=AppointmentKind.OPERATION,
            status=Status.ACTIVE
        )

        # search data
        data1 = {
            'keyword': 'bbc',
        }

        data2 = {
            'keyword': 'test',
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
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check with first keyword
        self.assertEqual(request.data['count'], 0)
        # check with another keyword
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)
        self.assertEqual(request.data['count'], 10)

        # delete first entry
        appointment_session[0].delete()

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if the results count is similler to 9
        self.assertEqual(request.data['count'], 9)

        # logout
        self.client.logout()
