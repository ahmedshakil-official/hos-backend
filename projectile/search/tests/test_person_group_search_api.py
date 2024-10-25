from django.urls import reverse
from common.test_case import OmisTestCase
from core.tests import PersonGroupFactory


class PersonGroupSearchAPITest(OmisTestCase):
    url = reverse('person-group-search')

    def test_person_group_search_get(self):
        person_group = PersonGroupFactory(
            organization=self.admin_user.organization
        )

        # search data
        data1 = {
            'keyword': 'search',
        }

        data2 = {
            'keyword': person_group.name,
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check with first keyword
        self.assertEqual(request.data['count'], 0)

        # check with another keyword
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()
