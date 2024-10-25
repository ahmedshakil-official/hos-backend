from django.urls import reverse

from common.test_case import OmisTestCase
from clinic.tests import (ServiceConsumedFactory,
                          ServiceConsumedGroupFactory,
                          SubServiceReportFieldNormalValueFactory,
                          SubServiceReportFieldFactory, )


class PathologyStandardValueSearchAPITest(OmisTestCase):
    url = reverse('pathology-standard-value-search')

    # def setUp(self):
    #     super(PathologyStandardValueSearchAPITest, self).setUp()

    def test_pathology_standart_search_request_get(self):
        sub_service_report_field = SubServiceReportFieldFactory(
            name='test',
            organization=self.admin_user.organization
        )
        standard_value = SubServiceReportFieldNormalValueFactory.create_batch(
            2,
            sub_service_report_field=sub_service_report_field
        )

        # search data
        data1 = {
            'keyword': 'test'
        }

        data2 = {
            'keyword': 'ttst'
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login but not as admin
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        self.client.logout()

        # ===========================================
        #  Check with login but as admin and owner
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        # delete first data
        standard_value[0].delete()

        request = self.client.get(self.url, data1)
        self.assertSuccess(request)
        self.assertEqual(request.data['count'], 1)
        self.assertEqual(
            request.data['results'][0]['alias'],
            str(standard_value[1].alias))
        self.assertEqual(
            request.data['results'][0]['id'],
            standard_value[1].id)

        # check with another keywod
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 0)
        # logout
        self.client.logout()
