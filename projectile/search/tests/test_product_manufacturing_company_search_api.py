from django.urls import reverse
from common.test_case import OmisTestCase
from pharmacy.tests import ProductManufacturingCompanyFactory
from common.enums import Status


class ProductManufacturingCompanySearchAPITest(OmisTestCase):
    url = reverse('pharmacy.product.manufacturer-search')

    # def setUp(self):
    #     super(ProductManufacturingCompanySearchAPITest, self).setUp()

    def test_product_manufacturing_company_search_get(self):
        ProductManufacturingCompanyFactory.create_batch(
            10,
            name="test",
            status=Status.ACTIVE,
            organization=self.admin_user.organization
        )

        # search data
        data1 = {
            'keyword': 'search',
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

        self.assertEqual(request.data['count'], 10)
        

        # logout
        self.client.logout()
