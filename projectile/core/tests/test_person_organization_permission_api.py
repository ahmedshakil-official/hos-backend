import json
from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status
from . import (
    PersonOrganizationGroupPermissionFactory,
    PersonOrganizationFactory,
    GroupPermissionFactory,
)


class PersonOrganizationPermissionListAPITest(OmisTestCase):
    url = reverse('person-organization-permission-list')

    def setUp(self):
        super(PersonOrganizationPermissionListAPITest, self).setUp()

    def test_person_organization_permission_list_get(self):
        person_organization_permission = PersonOrganizationGroupPermissionFactory(
            person_organization__organization=self.user.organization, status=Status.ACTIVE
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


        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # compare request data with created data
        self.assertEqual(request.data['count'], 1)
        self.assertEqual(
            request.data['results'][0]['person_organization']['alias'],
            str(person_organization_permission.person_organization.alias)
        )
        self.assertEqual(
            request.data['results'][0]['permission']['name'],
            person_organization_permission.permission.name
        )

        # logout
        self.client.logout()

    def test_person_organization_permission_list_post(self):

        # ===========================================
        #  Check without login
        # ===========================================
        data = {
            'permission_list': [
                {
                    'person_organization': PersonOrganizationFactory(organization=self.user.organization).id,
                    'permission': GroupPermissionFactory().id
                }
            ],
            'person_organization': PersonOrganizationFactory(organization=self.user.organization).id
        }
        request = self.client.post(self.url, data=json.dumps(
            dict(data)), content_type='application/json')
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.post(self.url, data=json.dumps(
            dict(data)), content_type='application/json')
        self.assertCreated(request)

        self.assertEqual(
            request.data[0]['person_organization'],
            data['permission_list'][0]['person_organization']
        )
        self.assertEqual(request.data[0]['permission'], data['permission_list'][0]['permission'])



class PersonOrganizationPermissionDetailsAPITest(OmisTestCase):

    def setUp(self):
        super(PersonOrganizationPermissionDetailsAPITest, self).setUp()

        self.person_organization_permission = PersonOrganizationGroupPermissionFactory(
            person_organization__organization=self.user.organization, status=Status.ACTIVE)
        self.url = reverse('person-organization-permission-details',
                           args=[self.person_organization_permission.alias])

    def test_person_organization_permission_details_get(self):
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
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)

         # compare request data with created data
        self.assertEqual(
            request.data['person_organization']['person']['first_name'],
            self.person_organization_permission.person_organization.person.first_name)
        self.assertEqual(
            request.data['person_organization']['alias'],
            str(self.person_organization_permission.person_organization.alias)
        )

        # logout
        self.client.logout()

    def test_person_organization_permission_details_put(self):
        data = {
            'person_organization': PersonOrganizationFactory(organization=self.user.organization).id,
            'permission': GroupPermissionFactory().id,
            'status': Status.ACTIVE
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

        self.assertEqual(
            request.data['person_organization'],
            data['person_organization'])
        self.assertEqual(request.data['permission'], data['permission'])

        # logout
        self.client.logout()

    def test_person_organization_permission_details_delete(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.delete(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.delete(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.delete(self.url)
        self.assertDeleted(request)

        request = self.client.get(self.url)
        self.assertNotFound(request)

        # logout
        self.client.logout()
