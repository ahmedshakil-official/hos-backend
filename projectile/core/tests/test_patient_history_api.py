from faker import Faker

from django.urls import reverse

from common.utils import inactive_instance
from common.test_case import OmisTestCase

from prescription.tests import MedicalRecordFactory


class MedicalRecordListAPITest(OmisTestCase):
    url = reverse('patient-history')
    fake = Faker()

    def setUp(self):
        super(MedicalRecordListAPITest, self).setUp()

    def test_medical_record_list_get(self):
        medical_record_will_be_deleted = MedicalRecordFactory.create_batch(
            2, organization=self.user.organization
        )

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
        # check if it is the same user
        self.assertEqual(request.data['count'], 0)

        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        inactive_instance(medical_record_will_be_deleted[0])

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()
