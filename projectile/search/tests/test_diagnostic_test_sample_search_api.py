from django.urls import reverse

from common.test_case import OmisTestCase
from clinic.tests import DiagnosticTestSampleFactory


class DiagnosticTestSampleSearchAPITest(OmisTestCase):
    url = reverse('diagnostic-test-sample-search')

    # def setUp(self):
    #     super(DiagnosticTestSampleSearchAPITest, self).setUp()

    def test_diagnostic_sample_test_search_get(self):
        sample_test = DiagnosticTestSampleFactory.create_batch(
            2, name='test test',
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

        # check if it is the same user and the keyword 'coo'
        self.assertEqual(request.data['count'], 0)


        # check with another keyword 'test'
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 2)

        # delete an instance and check again
        sample_test[0].delete()

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()
