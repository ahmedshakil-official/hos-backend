import json
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase

from ..tests import ProductFormFactory
from ..models import ProductForm


class ProductFormListAPITest(OmisTestCase):
    url = reverse('pharmacy.product.form-list')
    fake = Faker()

    def setUp(self):
        super(ProductFormListAPITest,self).setUp()

    def test_product_form_list_get(self):
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

        product_form_will_be_deleted = ProductFormFactory.create_batch(2, organization=self.admin_user.organization)

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        product_form_will_be_deleted[0].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        ProductFormFactory()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # admin user logout
        self.client.logout()

    def test_product_form_list_post(self):
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
        self.assertEqual(ProductForm.objects.count(), 1)

        # admin user logout
        self.client.logout()


class ProductFormDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(ProductFormDetailsAPITest,self).setUp()

        # set a product form
        self.admin_user_product_form = ProductFormFactory(
            organization=self.admin_user.organization)

        # set the url
        self.url = reverse('pharmacy.product.form-details', args=[self.admin_user_product_form.alias])

    def test_product_form_details_get(self):
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

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================

        # self.admin_user.organization = self.user.organization
        # self.admin_user.save()
        # request = self.client.get(self.url)
        self.assertSuccess(request)
        self.assertEqual(request.data['id'], self.admin_user_product_form.id)

        # admin user logout
        self.client.logout()

    def test_product_form_details_put(self):
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

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================

        #self.admin_user.organization = self.user.organization
        #self.admin_user.save()
        request = self.client.put(self.url, data=json.dumps(dict(data)), content_type='application/json')
        self.assertSuccess(request)
        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['description'], data['description'])

        # admin user logout
        self.client.logout()


# class ProductFormSearchAPITest(OmisTestCase):
#     url = reverse('pharmacy.product.form-search')
#     fake = Faker()

#     def setUp(self):
#         super(ProductFormSearchAPITest,self).setUp()

#     def test_product_form_list_get(self):
#         login = self.client.login(phone=self.admin_user.phone, password='testpass')
#         self.assertTrue(login)

#         # search keyword
#         data = {
#             'keyword': 'CO'
#         }

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # total existing searches for 'c'
#         total_existing_searches_data = request.data['count']

#         # logout
#         self.client.logout()


#         # Create a persion to compare
#         ProductFormFactory(name="COT", organization=self.admin_user.organization)

#         # first create some persons
#         d1 = ProductFormFactory(name="COM")
#         d2 = ProductFormFactory(name="CON")


#         # ===========================================
#         #  Check without login
#         # ===========================================
#         request = self.client.get(self.url, data)
#         self.assertPermissionDenied(request)

#         # ===========================================
#         #  Check with login
#         # ===========================================
#         login = self.client.login(phone=self.user.phone, password='testpass')
#         self.assertTrue(login)
#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # ===========================================
#         #  Check for admin user
#         # ===========================================
#         login = self.client.login(phone=self.admin_user.phone, password='testpass')
#         self.assertTrue(login)
#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         total_new_searches_data = request.data['count']
#         self.assertEqual(total_new_searches_data, total_existing_searches_data + 1)

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
#         self.assertEqual(request.data['count'], total_new_searches_data + 2)

#         d1.delete()

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], total_new_searches_data + 1)

#         # # logout
#         self.client.logout()
