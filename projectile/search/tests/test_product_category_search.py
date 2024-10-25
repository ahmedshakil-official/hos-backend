from django.urls import reverse
from common.test_case import OmisTestCase
from pharmacy.tests import ProductCategoryFactory
from faker import Faker


class ProductCategorySearchAPITest(OmisTestCase):
    url = reverse('pharmacy.product.category-search')
    fake = Faker()


    # def setUp(self):
    #     super(ProductCategorySearchAPITest,self).setUp()

    def test_product_category_search_get(self):
        product_name = self.fake.first_name()
        product_category = ProductCategoryFactory.create_batch(
            10,
            organization=self.admin_user.organization,
            name=product_name
        )

        #search
        data1 = {
            'keyword': 'search'
        }

        data2 = {
            'keyword': str(product_name)
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

        self.assertEqual(request.data['count'], 10)

        # logout
        self.client.logout()
