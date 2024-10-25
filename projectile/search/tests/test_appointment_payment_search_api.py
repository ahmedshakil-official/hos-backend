# from django.urls import reverse
# from common.test_case import OmisTestCase
# from clinic.tests import AppointmentPaymentFactory, AppointmentTreatmentSessionFactory
# from core.tests import PatientFactory
# from common.enums import PublishStatus, Status


# class AppointmentPaymentSearchAPITest(OmisTestCase):
#     url = reverse('appointment-payment-search')

#     # def setUp(self):
#     #     super(AppointmentPaymentSearchAPITest, self).setUp()

#     def test_appointment_payment_search_get(self):
#         person = PatientFactory(
#             organization=self.admin_user.organization,
#             first_name="test", last_name="test"
#         )
#         appointment = AppointmentTreatmentSessionFactory(
#             person=person,
#             organization=self.admin_user.organization
#         )
#         appointment_payment = AppointmentPaymentFactory.create_batch(
#             2,
#             appointment=appointment,
#             organization=self.admin_user.organization,
#             status=Status.ACTIVE
#         )

#          # search data
#         data1 = {
#             'keyword': 'les',
#         }

#         data2 = {
#             'keyword': 'test',
#         }

#         # ===========================================
#         #  Check without login
#         # ===========================================
#         request = self.client.get(self.url, data1)
#         self.assertPermissionDenied(request)

#         # ===========================================
#         #  Check with login
#         # ===========================================
#         login = self.client.login(phone=self.user.phone, password='testpass')
#         self.assertTrue(login)
#         request = self.client.get(self.url, data1)
#         self.assertPermissionDenied(request)

#         # ===========================================
#         #  Check for admin user
#         # ===========================================
#         login = self.client.login(
#             phone=self.admin_user.phone, password='testpass')
#         self.assertTrue(login)
#         request = self.client.get(self.url, data1)
#         self.assertSuccess(request)

#         # ===========================================
#         #  Check for admin user of the same organization
#         # ===========================================
#         request = self.client.get(self.url, data1)
#         self.assertSuccess(request)

#         # check with first keyword
#         self.assertEqual(request.data['count'], 0)

#         # check with another keyword
#         request = self.client.get(self.url, data2)
#         self.assertSuccess(request)

#         self.assertEqual(request.data['count'], 2)
#         self.assertEqual(
#             request.data['results'][0]['id'],
#             appointment_payment[1].id)
#         self.assertEqual(
#             request.data['results'][0]['alias'],
#             str(appointment_payment[1].alias))

#         self.assertEqual(
#             request.data['results'][1]['id'],
#             appointment_payment[0].id)
#         self.assertEqual(
#             request.data['results'][1]['alias'],
#             str(appointment_payment[0].alias))

#         # Delete one prescriber instance
#         appointment_payment[0].delete()
#         request = self.client.get(self.url, data2)
#         self.assertSuccess(request)

#         self.assertEqual(request.data['count'], 1)
#         # logout
#         self.client.logout()
