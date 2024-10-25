from faker import Faker
from django.urls import reverse
from common.test_case import OmisTestCase
from pharmacy.tests import ProductFactory, ProductGroupFactory, ProductSubGroupFactory
from common.enums import Status, PublishStatus


class ProductSearchAPITest(OmisTestCase):
    url = reverse('pharmacy.product-search')
    fake = Faker()

    # def setUp(self):
    #     super(ProductSearchAPITest, self).setUp()

    def test_product_search_get(self):
        product_name = self.fake.first_name()
        product__strength = self.fake.first_name()
        ProductFactory.create_batch(
            10,
            name=product_name,
            strength=product__strength,
            is_global=PublishStatus.PRIVATE,
            status=Status.ACTIVE,
            organization=self.admin_user.organization,
            is_service=False
        )

        # search data
        data1 = {
            'keyword': 'lse',
        }

        data2 = {
            'keyword': str(product_name + ' ' + product__strength),
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
