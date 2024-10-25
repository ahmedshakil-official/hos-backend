# from faker import Faker
# import uuid
# from django.urls import reverse
# from common.test_case import OmisTestCase
# from core.tests import PatientFactory


# class PersonOrganizationPatientListSearchAPITest(OmisTestCase):
#     url = reverse('person-organization-patient-search')
#     fake = Faker()

#     # def setUp(self):
#     #     super(PersonOrganizationPatientListSearchAPITest, self).setUp()

#     def test_person_organization_patient_list_search_get(self):
#         test_email = 'test@test.test' + str(uuid.uuid4())
#         person = PatientFactory.create_batch(
#             2, email=test_email,
#             organization=self.admin_user.organization
#         )

#         # search data
#         data1 = {
#             'keyword': 'les',
#         }

#         data2 = {
#             'keyword': test_email,
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

#         # self.assertEqual(
#         #     request.data['results'][0]['first_name'],
#         #     person[1].first_name)
#         # self.assertEqual(
#         #     request.data['results'][0]['last_name'],
#         #     person[1].last_name)
#         # self.assertEqual(
#         #     request.data['results'][0]['email'],
#         #     person[1].email)

#         # logout
#         self.client.logout()
