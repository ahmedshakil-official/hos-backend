from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import PublishStatus, Status

from clinic.tests import SubServiceFactory, ServiceFactory
from clinic.enums import ServiceType


class DiagnosticSubServiceSearchAPITest(OmisTestCase):
    url = reverse('sub-service-search')

    # def setUp(self):
    #     super(DiagnosticSubServiceSearchAPITest, self).setUp()

    def test_diagnostic_sub_service_search_get(self):
        service = ServiceFactory(type=ServiceType.DIAGNOSTIC)
        sub_service = SubServiceFactory.create_batch(
            2,
            name="test",
            service=service,
            organization=self.admin_user.organization,
            is_global=PublishStatus.INITIALLY_GLOBAL,
            status=Status.ACTIVE
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

        self.assertEqual(
            request.data['results'][0]['name'],
            sub_service[1].name)
        self.assertEqual(
            request.data['results'][0]['alias'],
            str(sub_service[1].alias))

        self.assertEqual(
            request.data['results'][1]['name'],
            sub_service[0].name)
        self.assertEqual(
            request.data['results'][1]['alias'],
            str(sub_service[0].alias))

        # logout
        self.client.logout()
