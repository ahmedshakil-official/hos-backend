from django.urls import reverse
from common.test_case import OmisTestCase
from clinic.tests import ServiceFactory


class ServiceSearchAPITest(OmisTestCase):
    url = reverse('service-search')

    # def setUp(self):
    #     super(ServiceSearchAPITest, self).setUp()

    def test_service_search_get(self):
        service = ServiceFactory.create_batch(
            2,
            name="test",
            organization=self.admin_user.organization
        )

        # search data
        data1 = {
            'keyword': 'les',
        }

        data2 = {
            'keyword': 'test',
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
        self.assertPermissionDenied(request)
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

        self.assertEqual(request.data['count'], 2)

        # delete first data
        service[0].delete()

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)
        self.assertEqual(request.data['count'], 1)

        self.assertEqual(
            request.data['results'][0]['name'],
            service[1].name)
        self.assertEqual(
            request.data['results'][0]['alias'],
            str(service[1].alias))
        self.assertEqual(
            request.data['results'][0]['discount'],
            service[1].discount)
        # logout
        self.client.logout()
