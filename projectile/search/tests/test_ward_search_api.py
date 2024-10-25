from django.urls import reverse

from common.test_case import OmisTestCase
from clinic.tests import WardFactory


class WardSearchAPITest(OmisTestCase):
    url = reverse('ward-search')

    # def setUp(self):
    #     super(WardSearchAPITest, self).setUp()

    def test_ward_search_get(self):
        ward = WardFactory.create_batch(
            2,
            name='test test',
            organization=self.admin_user.organization
            )

        # search data
        data1 = {
            'keyword': 'coo'
        }

        data2 = {
            'keyword': 'test'
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
        self.assertEqual(request.data['count'], 0)


        # check with another keywod
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 2)

        # logout
        self.client.logout()
