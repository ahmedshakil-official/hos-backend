from faker import Faker

from django.urls import reverse
from common.test_case import OmisTestCase
from common.enums import Status
from core.tests import OrganizationFactory


class OrganizationDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(OrganizationDetailsAPITest, self).setUp()

        # create an organization
        self.organization = OrganizationFactory()

        # set the url
        self.url = reverse('organization-details', args=[self.organization.alias])

    def test_organization_details_get(self):
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

        # user logout
        self.client.logout()

        # ===========================================
        #  Check with admin user
        # ===========================================
        self.admin_user.is_superuser = True
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)

        # admin user logout
        self.client.logout()

    def test_organization_details_put(self):
        data = {
            'name': self.fake.first_name(),
            'address': self.fake.last_name(),
            'primary_mobile': self.fake.msisdn(),
            'contact_person': self.fake.last_name(),
            'contact_person_designation': self.fake.first_name(),
            # 'slogan': self.fake.ssn(),
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.put(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.put(self.url, data)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check with admin user
        # ===========================================
        self.admin_user.is_superuser = True
        self.admin_user.save()
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.put(self.url, data)
        self.assertSuccess(request)

        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['address'], data['address'])
        self.assertEqual(request.data['primary_mobile'], data['primary_mobile'])

        # admin user logout
        self.client.logout()

    def test_organization_details_patch(self):
        data = {
            'status': Status.INACTIVE,
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.put(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.put(self.url, data)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check with admin user
        # ===========================================
        self.admin_user.is_superuser = True
        self.admin_user.save()
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.patch(self.url, data)
        self.assertSuccess(request)

        # compare request data with created data
        self.assertEqual(request.data['status'], data['status'])
        # admin user logout
        self.client.logout()
