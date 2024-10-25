import json
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase

from pharmacy.tests import ProductGenericFactory
from pharmacy.models import ProductGeneric



class ProductGenericListAPITest(OmisTestCase):
    url = reverse('pharmacy.product.generic-list')
    fake = Faker()

    def setUp(self):
        super(ProductGenericListAPITest,self).setUp()

    def test_product_generic_list_get(self):
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

        product_generic_will_be_deleted = \
            ProductGenericFactory.create_batch(2, organization=self.admin_user.organization)

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        product_generic_will_be_deleted[0].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        ProductGenericFactory()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # admin user logout
        self.client.logout()

    def test_product_generic_list_post(self):
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
        self.assertEqual(ProductGeneric.objects.count(), 1)

        # admin user logout
        self.client.logout()


class ProductGenericDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(ProductGenericDetailsAPITest,self).setUp()

        # set a product generic
        self.admin_user_product_generic = ProductGenericFactory(
            organization=self.admin_user.organization)

        # set the url
        self.url = reverse('pharmacy.product.generic-details', args=[self.admin_user_product_generic.alias])

    def test_product_generic_details_get(self):
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
            request.data['id'], self.admin_user_product_generic.id)

        # admin user logout
        self.client.logout()

    def test_product_generic_details_put(self):
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


    def test_product_generic_details_delete(self):
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
        self.assertEqual(ProductGeneric.objects.count(), 1)
        request = self.client.delete(self.url)
        self.assertDeleted(request)
        # admin user logout
        self.client.logout()


# class ProductGenericSearchAPITest(OmisTestCase):
#     url = reverse('pharmacy.product.generic-search')
#     fake = Faker()

#     def setUp(self):
#         super(ProductGenericSearchAPITest,self).setUp()

#     def test_product_generic_list_get(self):
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

#         # first create some persons
#         ProductGenericFactory(name="COX", organization=self.admin_user.organization)
#         d1 = ProductGenericFactory(name="COD")
#         d2 = ProductGenericFactory(name="COE")

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
#         # self.assertPermissionDenied(request)
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
