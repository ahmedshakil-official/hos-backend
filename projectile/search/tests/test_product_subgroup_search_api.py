from django.urls import reverse
from common.test_case import OmisTestCase
from pharmacy.tests import ProductSubGroupFactory


class ProductSubgroupSearchAPITest(OmisTestCase):
    url = reverse('pharmacy.product.subgroup-search')

    # def setUp(self):
    #     super(ProductSubgroupSearchAPITest, self).setUp()

    def test_product_subgroup_search_get(self):
        subgroups = ProductSubGroupFactory.create_batch(
            3,
            name='test',
            organization=self.admin_user.organization
        )
        data1 = {
            'keyword': 'nest'
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
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check if data1 keyword returns zero search result
        self.assertEqual(request.data['count'], 0)

        # check with data2 keyword
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if data2 keyword returns three search result
        self.assertEqual(request.data['count'], 3)

        # delete first entry
        subgroups[0].delete()

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if it is now returns two result after deletion
        self.assertEqual(request.data['count'], 2)

        # logout
        self.client.logout()
