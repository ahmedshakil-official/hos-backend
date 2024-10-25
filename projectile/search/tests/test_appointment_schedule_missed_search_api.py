from django.urls import reverse
from common.test_case import OmisTestCase
from common.enums import PublishStatus, Status
from clinic.tests import AppointmentScheduleMissedFactory, AppointmentScheduleFactory, TreatmentSessionFactory


class AppointmentScheduleSearchAPITest(OmisTestCase):
    url = reverse('appointment-missed-schedule-search')

    # def setUp(self):
    #     super(AppointmentScheduleSearchAPITest, self).setUp()

    def test_treatment_session_search_get(self):
        treatment_session = TreatmentSessionFactory(
            name="test",
            organization=self.admin_user.organization,
            status=Status.ACTIVE
        )

        appointment_schedule = AppointmentScheduleFactory(
            treatment_session=treatment_session,
            organization=self.admin_user.organization,
            status=Status.ACTIVE
            )
        appointment_missed_schedule = AppointmentScheduleMissedFactory.create_batch(
            2,
            organization=self.admin_user.organization,
            appointment_schedule=appointment_schedule
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

        # delete first data
        appointment_missed_schedule[0].delete()

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)
        self.assertEqual(request.data['count'], 1)

        self.assertEqual(
            request.data['results'][0]['id'],
            appointment_missed_schedule[1].id)
        self.assertEqual(
            request.data['results'][0]['alias'],
            str(appointment_missed_schedule[1].alias))

        # logout
        self.client.logout()
