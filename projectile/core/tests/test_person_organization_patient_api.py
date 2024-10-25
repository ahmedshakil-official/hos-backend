# import json
# from faker import Faker
# from django.urls import reverse
# from core.enums import PersonGroupType
# from common.test_case import OmisTestCase
# from . import PatientFactory
# from ..enums import PersonGender
# from ..models import PersonOrganization


# class PersonOrganizationPatientListAPITest(OmisTestCase):
#     url = reverse('person-organization-patient-list')
#     fake = Faker()

#     def setUp(self):
#         super(PersonOrganizationPatientListAPITest, self).setUp()

#     def test_person_organization_patient_list_get(self):
#         # ===========================================
#         #  Check without login
#         # ===========================================
#         request = self.client.get(self.url)
#         self.assertPermissionDenied(request)

#         # ===========================================
#         #  Check with login
#         # ===========================================
#         login = self.client.login(phone=self.user.phone, password='testpass')
#         self.assertTrue(login)
#         request = self.client.get(self.url)
#         self.assertPermissionDenied(request)

#         # user logout
#         self.client.logout()

#         # ===========================================
#         #  Check for admin user
#         # ===========================================
#         login = self.client.login(
#             phone=self.admin_user.phone,
#             password='testpass'
#         )
#         self.assertTrue(login)

#         person = PatientFactory.create_batch(
#             2, organization=self.admin_user.organization
#         )

#         request = self.client.get(self.url)
#         self.assertSuccess(request)

#         self.assertEqual(request.data['results'][0]['code'], person[1].code)
#         self.assertEqual(request.data['results'][0]['first_name'], person[1].first_name)
#         self.assertEqual(request.data['results'][0]['last_name'], person[1].last_name)
#         self.assertEqual(request.data['results'][0]['email'], person[1].email)

#         query_from_database = PersonOrganization.objects.filter(
#             organization=self.admin_user.organization,
#             person_group=PersonGroupType.PATIENT
#         ).count()

#         self.assertEqual(request.data['count'], query_from_database)

#         query_from_database = PersonOrganization.objects.filter(
#             organization=self.admin_user.organization,
#             person_group=PersonGroupType.PATIENT
#         ).count()

#         # check if it is the same user
#         self.assertEqual(request.data['count'], query_from_database)

#         # create a person without organization
#         PatientFactory()

#         query_from_database = PersonOrganization.objects.filter(
#             organization=self.admin_user.organization,
#             person_group=PersonGroupType.PATIENT
#         ).count()

#         # if organization is not created then query data will be same as before
#         self.assertEqual(request.data['count'], query_from_database)

#         request = self.client.get(self.url)
#         self.assertSuccess(request)

#         # now create with organization
#         PatientFactory(organization=self.admin_user.organization)
#         request = self.client.get(self.url)

#         query_from_database = PersonOrganization.objects.filter(
#             organization=self.admin_user.organization,
#             person_group=PersonGroupType.PATIENT
#         ).count()

#         # Now query return exact number of data
#         self.assertEqual(request.data['count'], query_from_database)

#         # admin user logout
#         self.client.logout()



# class PersonOrganizationPatientDetailsAPITest(OmisTestCase):
#     fake = Faker()

#     def setUp(self):
#         super(PersonOrganizationPatientDetailsAPITest, self).setUp()
#         self.patient = PatientFactory(organization=self.admin_user.organization)
#         self.person_organization = PersonOrganization.objects.filter(
#             organization=self.admin_user.organization, person=self.patient
#         ).first()
#         self.url = reverse(
#             'person-organization-patient-details', args=[self.person_organization.alias])

#     def test_person_organization_patient_details_get(self):
#         # ===========================================
#         #  Check without login
#         # ===========================================
#         request = self.client.get(self.url)
#         self.assertPermissionDenied(request)

#         # ===========================================
#         #  Check with login
#         # ===========================================
#         login = self.client.login(phone=self.user.phone, password='testpass')
#         self.assertTrue(login)
#         request = self.client.get(self.url)
#         self.assertPermissionDenied(request)

#         # ===========================================
#         #  Check for admin user
#         # ===========================================
#         login = self.client.login(
#             phone=self.admin_user.phone, password='testpass')
#         self.assertTrue(login)

#         request = self.client.get(self.url)
#         self.assertSuccess(request)
#         # check if it is the same instance
#         self.assertEqual(request.data['id'], self.person_organization.pk)
#         self.assertEqual(request.data['first_name'], self.person_organization.first_name)
#         self.assertEqual(request.data['last_name'], self.person_organization.last_name)
#         self.assertEqual(request.data['phone'], self.person_organization.phone)

#         # logout
#         self.client.logout()

#     def test_person_organization_patient_details_put(self):
#         data = {
#             'first_name': self.fake.first_name(),
#             'last_name': self.fake.last_name(),
#             'phone': self.fake.msisdn(),
#             'gender':  PersonGender.MALE,
#             'dob': self.fake.date(pattern="%Y-%m-%d")
#         }
#         # ===========================================
#         #  Check without login
#         # ===========================================
#         request = self.client.put(self.url, data)
#         self.assertPermissionDenied(request)

#         # ===========================================
#         #  Check with login
#         # ===========================================
#         login = self.client.login(phone=self.user.phone, password='testpass')
#         self.assertTrue(login)
#         request = self.client.put(self.url, data)
#         self.assertPermissionDenied(request)

#         # ===========================================
#         #  Check with admin user
#         # ===========================================
#         login = self.client.login(
#             phone=self.admin_user.phone, password='testpass')
#         self.assertTrue(login)
#         request = self.client.put(self.url, data=json.dumps(
#             dict(data)), content_type='application/json')
#         self.assertSuccess(request)
#         self.assertEqual(request.data['first_name'], data['first_name'])
#         self.assertEqual(request.data['last_name'], data['last_name'])
#         self.assertEqual(request.data['phone'], data['phone'])
#         self.assertEqual(request.data['gender'], data['gender'])
#         self.assertEqual(request.data['dob'], data['dob'])

#         # check with person model's data not equal to edited data in personOrganization
#         self.assertNotEqual(request.data['phone'], self.patient.phone)
#         self.assertNotEqual(request.data['first_name'], self.patient.first_name)
#         self.assertNotEqual(request.data['last_name'], self.patient.last_name)
#         self.assertNotEqual(request.data['dob'], self.patient.dob)

#         # logout
#         self.client.logout()
