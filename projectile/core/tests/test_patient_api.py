import json
import random
from faker import Faker
from django.urls import reverse

from common.enums import Status
from common.test_case import OmisTestCase
from . import PatientFactory, PersonOrganizationFactory
from ..enums import PersonGroupType, PersonGender
from ..models import Person



# class PatientSearchAPITest(OmisTestCase):
#     url = reverse('patient-search')
#     fake = Faker()

#     def setUp(self):
#         super(PatientSearchAPITest, self).setUp()

#     def test_patient_list_get(self):
#         # first create some persons
#         d1 = PatientFactory(first_name="cccEO")
#         d2 = PatientFactory(first_name="cccTO")

#         # search data
#         data = {
#             'keyword': 'ccc'
#         }

#         # ===========================================
#         #  Check without login
#         # ===========================================
#         request = self.client.get(self.url, data)
#         self.assertPermissionDenied(request)

#         # ===========================================
#         #  Check with login
#         # ===========================================
#         # login = self.client.login(phone=self.user.phone, password='testpass')
#         # self.assertTrue(login)
#         # request = self.client.get(self.url, data)
#         # self.assertPermissionDenied(request)

#         # ===========================================
#         #  Check for admin user
#         # ===========================================
#         login = self.client.login(
#             phone=self.admin_user.phone, password='testpass')
#         self.assertTrue(login)
#         # request = self.client.get(self.url, data)
#         # self.assertSuccess(request)
#         #
#         # # check if it is the same user
#         # self.assertEqual(request.data['count'], 0)

#         # ===============================================
#         #  Check for admin user of the same organization
#         # ===============================================
#         d1.organization = self.admin_user.organization
#         d1.save()
#         d2.organization = self.admin_user.organization
#         d2.save()

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 2)

#         d1.delete()

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 1)

#         # logout
#         self.client.logout()


class PatientAllInfoAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(PatientAllInfoAPITest, self).setUp()
        # create a designation
        self.organization_person = PersonOrganizationFactory(
            person_group=PersonGroupType.PATIENT,
            organization=self.admin_user.organization
        )

        self.url = reverse('patient-all-info', args=[self.organization_person.alias])

    def test_patient_all_info_get(self):
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
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['id'], self.organization_person.pk)

        # logout
        self.client.logout()
