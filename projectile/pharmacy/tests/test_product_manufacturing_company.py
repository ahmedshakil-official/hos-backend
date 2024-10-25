import json
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from pharmacy.tests import ProductManufacturingCompanyFactory
from pharmacy.models import ProductManufacturingCompany



class ProductManufacturingCompanyListAPITest(OmisTestCase):
    url = reverse('pharmacy.product.manufacturer-list')
    fake = Faker()

    def setUp(self):
        super(ProductManufacturingCompanyListAPITest,self).setUp()

    def test_product_manufacturing_company_list_get(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        product_manufacturing_company_will_be_deleted = \
            ProductManufacturingCompanyFactory.create_batch(2, organization=self.admin_user.organization)

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        product_manufacturing_company_will_be_deleted[0].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        ProductManufacturingCompanyFactory()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # admin user logout
        self.client.logout()

    def test_product_manufacturing_company_list_post(self):
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
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.post(self.url, data)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.post(self.url, data)
        self.assertCreated(request)
        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['description'], data['description'])
        self.assertEqual(ProductManufacturingCompany.objects.count(), 1)

        # admin user logout
        self.client.logout()


class ProductManufacturingCompanyDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(ProductManufacturingCompanyDetailsAPITest,self).setUp()

        # set a product manufacturing_company
        self.admin_user_product_manufacturing_company = \
            ProductManufacturingCompanyFactory(
                organization=self.admin_user.organization)

        # set the url
        self.url = reverse('pharmacy.product.manufacturer-details',
                           args=[self.admin_user_product_manufacturing_company.alias])

    def test_product_manufacturing_company_details_get(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        # self.assertPermissionDenied(request)

        # # ===========================================
        # #  Check with admin user of same organization
        # # ===========================================
        # self.admin_user.organization = self.user.organization
        # self.admin_user.save()
        # request = self.client.get(self.url)
        self.assertSuccess(request)
        self.assertEqual(
            request.data['id'],
            self.admin_user_product_manufacturing_company.id
        )

        # admin user logout
        self.client.logout()

    def test_product_manufacturing_company_details_put(self):
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
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.put(self.url, data)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.put(self.url, data=json.dumps(dict(data)), content_type='application/json')
        # self.assertPermissionDenied(request)

        # # ===========================================
        # #  Check with admin user of same organization
        # # ===========================================
        # self.admin_user.organization = self.user.organization
        # self.admin_user.save()
        # request = self.client.put(self.url, data=json.dumps(dict(data)), content_type='application/json')
        self.assertSuccess(request)
        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['description'], data['description'])

        # admin user logout
        self.client.logout()


    def test_product_manufacturing_company_details_delete(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.delete(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.delete(self.url)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        self.assertEqual(ProductManufacturingCompany.objects.count(), 1)
        request = self.client.delete(self.url)
        self.assertDeleted(request)

        # admin user logout
        self.client.logout()


# class ProductManufacturingCompanySearchAPITest(OmisTestCase):
#     url = reverse('pharmacy.product.manufacturer-search')
#     fake = Faker()

#     def setUp(self):
#         super(ProductManufacturingCompanySearchAPITest,self).setUp()

#     def test_product_manufacturing_company_list_get(self):
#         # first create some persons
#         ProductManufacturingCompanyFactory(name="COB", organization=self.admin_user.organization)
#         d1 = ProductManufacturingCompanyFactory(name="COY")
#         d2 = ProductManufacturingCompanyFactory(name="COE")

#         # ===========================================
#         #  Check without login
#         # ===========================================
#         request = self.client.get(self.url)
#         self.assertPermissionDenied(request)

#         # ===========================================
#         #  Check with login
#         # ===========================================
#         login = self.client.login(phone=self.user.phone, password='testpass')
#         self.assertTrue(login)
#         request = self.client.get(self.url)
#         self.assertPermissionDenied(request)

#         self.client.logout()
#         # ===========================================
#         #  Check for admin user
#         # ===========================================
#         data = {
#             'keyword': 'CO'
#         }
#         login = self.client.login(phone=self.admin_user.phone, password='testpass')
#         self.assertTrue(login)
#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         self.assertEqual(request.data['count'], 1)

#         # ===============================================
#         #  Check for admin user of the same organization
#         # ===============================================
#         d1.organization = self.admin_user.organization
#         d1.save()
#         d2.organization = self.admin_user.organization
#         d2.save()

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 3)
#         d1.delete()

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 2)

#         # # logout
#         self.client.logout()
