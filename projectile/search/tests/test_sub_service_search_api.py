from faker import Faker
from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import PublishStatus, Status

from clinic.tests import SubServiceFactory


class SubServiceSearchAPITest(OmisTestCase):
    url = reverse('sub-service-search')
    fake = Faker()

    def test_sub_service_search_get(self):
        sub_service_name = self.fake.first_name()
        SubServiceFactory.create_batch(
            10,
            name=sub_service_name,
            organization=self.admin_user.organization,
            is_global=PublishStatus.INITIALLY_GLOBAL,
            status=Status.ACTIVE
        )

        # search data
        data1 = {
            'keyword': 'search',
        }

        data2 = {
            'keyword': sub_service_name,
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

        self.assertEqual(request.data['count'], 10)


        # logout
        self.client.logout()
