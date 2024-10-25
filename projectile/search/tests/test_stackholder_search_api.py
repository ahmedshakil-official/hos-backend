from django.urls import reverse

from common.enums import Status
from common.test_case import OmisTestCase

from core.enums import PersonGroupType
from core.tests import PersonFactory


class StackHolderSearchAPITest(OmisTestCase):
    url = reverse('stack-holder-search')

    # def setUp(self):
    #     super(StackHolderSearchAPITest, self).setUp()

    def test_stack_holder_search_get(self):
        stackholder = PersonFactory(
            organization=self.admin_user.organization,
            status=Status.ACTIVE,
            first_name='test',
            last_name='text',
            person_group=PersonGroupType.STACK_HOLDER
        )

        # search data
        data1 = {
            'keyword': 'test'
        }

        data2 = {
            'keyword': 'testts'
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone,
            password='testpass'
        )
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone,
            password='testpass'
        )
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)
        self.assertEqual(
            request.data['results'][0]['first_name'], stackholder.first_name
        )
        self.assertEqual(
            request.data['results'][0]['last_name'], stackholder.last_name
        )

        # check with another keywod
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 0)

        # logout
        self.client.logout()
