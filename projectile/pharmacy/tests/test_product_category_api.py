import json
from django.urls import reverse
from faker import Faker

from common.test_case import OmisTestCase

from ..tests import ProductCategoryFactory
from ..models import ProductCategory


class ProductCategoryListAPITest(OmisTestCase):
    url = reverse('pharmacy.product.category-list')
    fake = Faker()

    def test_product_category_list_get(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(
            phone=self.user.phone,
            password='testpass'
        )
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone,
            password='testpass'
        )
        self.assertTrue(login)

        product_categories = ProductCategoryFactory.create_batch(
            3,
            name=self.fake.first_name(),
            organization=self.admin_user.organization
        )

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check 3 product category is created or not
        self.assertEqual(request.data['count'], 3)

        product_categories[0].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check after deletion product category is 2
        self.assertEqual(request.data['count'], 2)

        # admin user logout
        self.client.logout()

    def test_product_category_list_post(self):
        # ===========================================
        #  Check without login
        # ===========================================
        data = {
            'name': self.fake.first_name(),
            'description': self.fake.text(),
        }
        request = self.client.post(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(
            phone=self.user.phone,
            password='testpass'
        )
        self.assertTrue(login)

        request = self.client.post(self.url, data)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone,
            password='testpass'
        )
        self.assertTrue(login)
        request = self.client.post(self.url, data)
        self.assertCreated(request)

        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['description'], data['description'])
        self.assertEqual(ProductCategory.objects.count(), 1)

        # admin user logout
        self.client.logout()


class ProductCategoryDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(ProductCategoryDetailsAPITest, self).setUp()

        # set a product category
        self.admin_user_product_category = ProductCategoryFactory(
            organization=self.admin_user.organization
        )

        # set the url with alias
        self.url = reverse(
            'pharmacy.product.category-details',
            args=[self.admin_user_product_category.alias]
        )

    def test_product_category_details_get(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(
            phone=self.user.phone,
            password='testpass'
        )
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone,
            password='testpass'
        )
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check product alias is same or not
        self.assertEqual(
            request.data['alias'],
            str(self.admin_user_product_category.alias)
        )

        # admin user logout
        self.client.logout()

    def test_product_category_details_put(self):
        data = {
            'name': self.fake.first_name(),
            'description': self.fake.text(),
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.put(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(
            phone=self.user.phone,
            password='testpass'
        )
        self.assertTrue(login)
        request = self.client.put(self.url, data)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone,
            password='testpass'
        )
        self.assertTrue(login)
        request = self.client.put(self.url, data=json.dumps(
            dict(data)), content_type='application/json')

        # # ===========================================
        # #  Check with admin user of same organization
        # # ===========================================
        self.assertSuccess(request)
        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['description'], data['description'])

        # admin user logout
        self.client.logout()
