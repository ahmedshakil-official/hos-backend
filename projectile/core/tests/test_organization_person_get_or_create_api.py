from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status
from . import PatientFactory

class OrganizationPersonGetOrCreateAPITest(OmisTestCase):
    url = reverse('organization-person-get-or-create')

    def setUp(self):
        super(OrganizationPersonGetOrCreateAPITest, self).setUp()

    def test_organization_person_get_or_create_post(self):

        patient = PatientFactory(organization=self.user.organization)
        data = {
            'person': patient.id,
            'organization': patient.organization.id,
            'status': Status.ACTIVE
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.post(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.post(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.post(self.url, data)
        self.assertCreated(request)

        self.assertEqual(request.data['person'], data['person'])
        self.assertEqual(request.data['organization'], data['organization'])
