from django.urls import reverse
from common.test_case import OmisTestCase
from common.enums import PublishStatus
from prescription.tests import AdditionalInfoFactory


class AdditionalInfoSearchAPITest(OmisTestCase):
    url = reverse('prescription-additional-info-search')

    def test_additional_info_search_get(self):
        additional_info = AdditionalInfoFactory.create_batch(
            2,
            name="test",
            organization=self.admin_user.organization,
            is_global=PublishStatus.INITIALLY_GLOBAL
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
            request.data['results'][0]['id'],
            additional_info[1].id)
        self.assertEqual(
            request.data['results'][0]['name'],
            additional_info[1].name)
        self.assertEqual(
            request.data['results'][1]['alias'],
            str(additional_info[0].alias))
        self.assertEqual(
            request.data['results'][1]['id'],
            additional_info[0].id)
        self.assertEqual(
            request.data['results'][1]['name'],
            additional_info[0].name)
        self.assertEqual(
            request.data['results'][1]['alias'],
            str(additional_info[0].alias))

        # logout
        self.client.logout()
