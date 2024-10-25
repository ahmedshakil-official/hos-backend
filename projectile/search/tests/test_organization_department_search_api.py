from django.urls import reverse

from common.test_case import OmisTestCase
from clinic.tests import OrganizationDepartmentFactory


class OrganizationDepartSearchAPITest(OmisTestCase):
    url = reverse('organization-department-search')

    def test_organization_department_search_get(self):
        department = OrganizationDepartmentFactory(
            name='department1',
            description='test description',
            organization=self.admin_user.organization
        )

        # search data
        data1 = {
            'keyword': 'dep'
        }

        data2 = {
            'keyword': 'tes'
        }

        # ===========================================
        #   Check without login
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        # ===========================================
        #   Check with login
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone,
            password='testpass'
        )
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # ===========================================
        #   Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone,
            password='testpass'
        )
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # ===========================================
        #   Check with first keyword
        # ===========================================
        self.assertEqual(request.data['count'], 1)

        self.assertEqual(request.data['results'][0]['name'], department.name)
        self.assertEqual(
            request.data['results'][0]['description'],
            department.description
        )

        # ===========================================
        #   Check with second keyword
        # ===========================================
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 0)
        # ===========================================
        #   Logout
        # ===========================================
        self.client.logout()
