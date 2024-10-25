from django.urls import reverse
from common.test_case import OmisTestCase
from prescription.tests import LabTestFactory
from common.enums import Status, PublishStatus


class LabTestSearchAPITest(OmisTestCase):
    url = reverse('prescription-labtest-search')

    # def setUp(self):
    #     super(LabTestSearchAPITest, self).setUp()

    def test_labtest_search_get(self):
        labtest = LabTestFactory.create_batch(
            2,
            name="test",
            is_global = PublishStatus.PRIVATE,
            organization=self.admin_user.organization,
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
            labtest[1].name)
        self.assertEqual(
            request.data['results'][0]['alias'],
            str(labtest[1].alias))

        self.assertEqual(
            request.data['results'][1]['name'],
            labtest[0].name)
        self.assertEqual(
            request.data['results'][1]['alias'],
            str(labtest[0].alias))

        # logout
        self.client.logout()
