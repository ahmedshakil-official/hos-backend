from django.urls import reverse
from common.test_case import OmisTestCase
from clinic.tests import BedSectionFactory


class BedSectionSearchAPITest(OmisTestCase):
    url = reverse('bed-section-search')

    # def setUp(self):
    #     super(BedSectionSearchAPITest, self).setUp()

    def test_bed_section_search_get(self):
        bed_section = BedSectionFactory.create_batch(
            2,
            section_name="test_bed",
            organization=self.admin_user.organization
        )

        # search data
        data1 = {
            'keyword': 'demo',
        }

        data2 = {
            'keyword': 'test_b',
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
        bed_section[0].delete()

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)
        self.assertEqual(request.data['count'], 1)

        self.assertEqual(
            request.data['results'][0]['section_name'],
            bed_section[1].section_name)
        self.assertEqual(
            request.data['results'][0]['alias'],
            str(bed_section[1].alias))

        # logout
        self.client.logout()
