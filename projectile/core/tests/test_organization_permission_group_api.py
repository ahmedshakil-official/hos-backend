from django.urls import reverse
from faker import Faker

from common.test_case import OmisTestCase
from common.enums import Status
from . import GroupPermissionFactory


class OrganizationPermissionGroupListAPITest(OmisTestCase):
    url = reverse('organization-permission-group-list')
    fake = Faker()

    def setUp(self):
        super(OrganizationPermissionGroupListAPITest, self).setUp()

    def test_organization_permission_group_list_get(self):
        organization_permission_group = GroupPermissionFactory(status=Status.ACTIVE)

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


        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # compare request data with created data
        self.assertEqual(request.data['count'], 7)
        self.assertEqual(
            request.data['results'][self.countGroupPermission]['name'],
            organization_permission_group.name
        )
        self.assertEqual(
            request.data['results'][self.countGroupPermission]['description'],
            organization_permission_group.description
        )

        # logout
        self.client.logout()

    def test_person_organization_permission_list_post(self):

        # ===========================================
        #  Check without login
        # ===========================================
        data = {
            'name': self.fake.name(),
            'description': self.fake.text(),
        }

        request = self.client.post(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.post(self.url, data)
        self.assertCreated(request)

        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['description'], data['description'])



class OrganizationPermissionGroupDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(OrganizationPermissionGroupDetailsAPITest, self).setUp()

        self.organization_permission_group = GroupPermissionFactory(status=Status.ACTIVE)
        self.url = reverse(
            'organization-permission-group-details',
            args=[self.organization_permission_group.alias])

    def test_organization_permission_group_details_get(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # compare request data with created data
        self.assertEqual(request.data['name'], self.organization_permission_group.name)
        self.assertEqual(
            request.data['description'], self.organization_permission_group.description)

        # logout
        self.client.logout()

    def test_organization_permission_group_details_put(self):
        data = {
            'name': self.fake.name(),
            'description': self.fake.text(),
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

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.put(self.url, data)
        self.assertSuccess(request)

        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['description'], data['description'])

        # logout
        self.client.logout()

    def test_organization_permission_group_details_delete(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.delete(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.delete(self.url)
        self.assertDeleted(request)

        request = self.client.get(self.url)
        self.assertNotFound(request)

        # logout
        self.client.logout()
