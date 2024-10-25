from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import PublishStatus
from clinic.tests import InvestigationFieldFactory


class InvestigationFieldSearchAPITest(OmisTestCase):
    url = reverse('investigation-field-search')

    # def setUp(self):
    #     super(InvestigationFieldSearchAPITest, self).setUp()

    def test_investigation_field_search_get(self):
        InvestigationFieldFactory(
            name='omis',
            organization=self.admin_user.organization
        )
        InvestigationFieldFactory(
            name='omis global',
            is_global=PublishStatus.INITIALLY_GLOBAL
        )
        InvestigationFieldFactory(
            name='omis private global',
            is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL
        )

        # search data
        data1 = {
            'keyword': 'coo'
        }

        data2 = {
            'keyword': 'omis'
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
        self.assertEqual(request.data['count'], 3)

        # logout
        self.client.logout()
