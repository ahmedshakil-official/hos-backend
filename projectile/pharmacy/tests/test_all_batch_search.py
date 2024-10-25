from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase

from ..tests import StockIOLogFactory


class ProductAllBatchAPITest(OmisTestCase):
    url = reverse('pharmacy.all-product-batch-search')
    fake = Faker()

    def setUp(self):
        super(ProductAllBatchAPITest, self).setUp()

    def test_product_medicine_list_get(self):
        # first create some persons
        StockIOLogFactory(batch="MTC", organization=self.admin_user.organization)
        StockIOLogFactory(batch="CVTR", organization=self.admin_user.organization)

        # search data
        key = {
            'keyword': 'c'
        }

        key2 = {
            'keyword': 'cv'
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, key)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, key)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, key)
        self.assertSuccess(request)
        #check with keyword
        self.assertEqual(request.data['count'], 2)

        #checko with another keyword
        request = self.client.get(self.url, key2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 1)

        self.client.logout()
