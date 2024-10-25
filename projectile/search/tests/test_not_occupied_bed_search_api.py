from django.urls import reverse

from common.test_case import OmisTestCase
from clinic.tests import BedFactory
from clinic.enums import BedType


class NotOccupiedBedSearchAPITest(OmisTestCase):
    url = reverse('not-occupied-bed-search')

    # def setUp(self):
    #     super(NotOccupiedBedSearchAPITest, self).setUp()

    def test_not_occupied_search_get(self):
        # first create some bed
        BedFactory.create_batch(
            10, name='TEST',
            bed_type=BedType.ADMISSION_BED,
            organization=self.admin_user.organization
        )

        # search data
        data1 = {
            'keyword': 'ccc'
        }

        data2 = {
            'keyword': 'tes'
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
        self.assertEqual(request.data['count'], 10)

        # logout
        self.client.logout()
