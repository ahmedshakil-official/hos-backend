from django.urls import reverse
from common.test_case import OmisTestCase
from clinic.tests import AppointmentTreatmentSessionFactory
from clinic.enums import AppointmentKind
from core.tests import PersonOrganizationFactory
from clinic.enums import AppointmentType
from common.enums import PublishStatus, Status


class RequestedAppointmentTreatmentSessionSearchAPITest(OmisTestCase):
    url = reverse("requested-appointment-treatment-session-search")

    # def setUp(self):
    #     super(RequestedAppointmentTreatmentSessionSearchAPITest, self).setUp()

    def test_requested_appointment_treatment_session_search_get(self):
        person_organization = PersonOrganizationFactory(
            first_name='test',
            organization=self.admin_user.organization
        )
        AppointmentTreatmentSessionFactory.create_batch(
            2,
            person=person_organization.person,
            person_organization=person_organization,
            organization=self.admin_user.organization,
            status=Status.ACTIVE,
            kind=AppointmentKind.CONSULTATION,
            type=AppointmentType.REQUEST
        )

        # search data
        data1 = {
            'keyword': 'les',
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
        self.assertEqual(request.data['count'], 2)

        # logout
        self.client.logout()
