from faker import Faker
from django.urls import reverse
from common.test_case import OmisTestCase
from pharmacy.tests import ProductFactory, ProductGroupFactory, ProductSubGroupFactory
from common.enums import Status, PublishStatus
from pharmacy.enums import ProductGroupType


class ProductMedicineSearchAPITest(OmisTestCase):
    url = reverse('pharmacy.product-medicine-search')
    fake = Faker()

    # def setUp(self):
    #     super(ProductMedicineSearchAPITest, self).setUp()

    def test_product_medicine_search_get(self):
        group = ProductGroupFactory(name=self.fake.first_name(), type=ProductGroupType.MEDICINE)
        sub_group = ProductSubGroupFactory(product_group=group)
        product_name = self.fake.first_name()
        product_strength = self.fake.first_name()
        ProductFactory.create_batch(
            10,
            name=product_name,
            strength=product_strength,
            is_global=PublishStatus.PRIVATE,
            status=Status.ACTIVE,
            organization=self.admin_user.organization,
            subgroup=sub_group
        )

        # search data
        data1 = {
            'keyword': 'next',
        }

        data2 = {
            'keyword': str(product_name + ' ' + product_strength),
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
