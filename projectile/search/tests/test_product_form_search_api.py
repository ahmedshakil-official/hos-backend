from django.urls import reverse
from common.test_case import OmisTestCase
from pharmacy.tests import ProductFormFactory
from common.enums import Status


class ProductFormSearchAPITest(OmisTestCase):
    url = reverse('pharmacy.product.form-search')

    # def setUp(self):
    #     super(ProductFormSearchAPITest, self).setUp()

    def test_product_form_search_get(self):
        product_form = ProductFormFactory.create_batch(
            2,
            name="test",
            description = 'dt',
            status=Status.ACTIVE,
            organization=self.admin_user.organization
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

        self.assertEqual(request.data['count'], 2)
        self.assertEqual(
            request.data['results'][0]['name'],
            product_form[0].name)
        self.assertEqual(
            request.data['results'][0]['description'],
            product_form[0].description)

        self.assertEqual(
            request.data['results'][1]['name'],
            product_form[1].name)
        self.assertEqual(
            request.data['results'][1]['description'],
            product_form[1].description)

        # logout
        self.client.logout()
