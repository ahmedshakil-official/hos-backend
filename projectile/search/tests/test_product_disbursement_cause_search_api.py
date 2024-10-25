from django.urls import reverse
from common.test_case import OmisTestCase
from pharmacy.tests import ProductDisbursementCauseFactory
from faker import Faker


class ProductDisbursementCauseAPITest(OmisTestCase):
    url = reverse('pharmacy.product-disbursement-cause-search')
    fake = Faker()

    def test_product_disbursement_cause_search_get(self):
        product_disbursement_cause_name = self.fake.first_name()
        ProductDisbursementCauseFactory.create_batch(
            10,
            organization=self.admin_user.organization,
            name=product_disbursement_cause_name
        )

        #search
        data1 = {
            'keyword': 'search'
        }

        data2 = {
            'keyword': str(product_disbursement_cause_name)
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
