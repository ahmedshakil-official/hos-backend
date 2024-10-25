# from django.urls import reverse
# from common.test_case import OmisTestCase
# from core.tests import PatientFactory
# from prescription.tests import PrescriptionFactory


# class PersonOrganizationPatientListSearchAPITest(OmisTestCase):
#     url = reverse('patient-meta-search')

#     # def setUp(self):
#     #     super(PersonOrganizationPatientListSearchAPITest, self).setUp()

#     def test_person_organization_patient_list_search_get(self):
#         patient = PatientFactory(
#             email='test@test.test',
#             organization=self.admin_user.organization
#         )
#         patient_prescription = PrescriptionFactory.create_batch(
#             3, organization=self.admin_user.organization, patient=patient)

#         # search data
#         data1 = {
#             'keyword': 'les',
#         }

#         data2 = {
#             'keyword': 'tes',
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
#         self.assertSuccess(request)

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

#         self.assertEqual(request.data['count'], 1)


#         self.assertEqual(
#             request.data['results'][0]['total_prescription_count'], len(patient_prescription))

#         self.assertEqual(
#             request.data['results'][0]['first_name'],
#             patient.first_name)
#         self.assertEqual(
#             request.data['results'][0]['last_name'],
#             patient.last_name)

#         # logout
#         self.client.logout()
