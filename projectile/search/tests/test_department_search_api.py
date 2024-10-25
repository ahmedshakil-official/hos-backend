from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status
from core.tests import DepartmentFactory


class DepartmentSearchAPITest(OmisTestCase):
    url = reverse('department-search')

    # def setUp(self):
    #     super(DepartmentSearchAPITest, self).setUp()

    def test_department_search_get(self):
        department = DepartmentFactory(
            organization=self.admin_user.organization,
            status=Status.ACTIVE,
            name='test'
        )

        # search data
        data1 = {
            'keyword': 'test'
        }

        data2 = {
            'keyword': 'text'
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        self.assertEqual(
            request.data['results'][0]['name'], department.name
        )

        # check with another keywod
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 0)

        # logout
        self.client.logout()
