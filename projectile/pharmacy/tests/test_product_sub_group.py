import json
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase

from pharmacy.tests import ProductGroupFactory, ProductSubGroupFactory
from pharmacy.models import ProductSubgroup


class ProductSubGroupListAPITest(OmisTestCase):
    url = reverse('pharmacy.product.subgroup-list')
    fake = Faker()

    def setUp(self):
        super(ProductSubGroupListAPITest,self).setUp()

    def test_product_sub_group_list_get(self):
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

        product_sub_group_will_be_deleted = \
            ProductSubGroupFactory.create_batch(2, organization=self.admin_user.organization)

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        product_sub_group_will_be_deleted[0].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        ProductSubGroupFactory()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # admin user logout
        self.client.logout()

    def test_product_sub_group_list_post(self):
        # ===========================================
        #  Check without login
        # ===========================================
        data = {
            'name': self.fake.first_name(),
            'description': self.fake.text(),
            'product_group': ProductGroupFactory().pk
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
        self.assertEqual(request.data['product_group'], data['product_group'])
        self.assertEqual(ProductSubgroup.objects.count(), 1)

        # admin user logout
        self.client.logout()


class ProductSubGroupDetailsAPITest(OmisTestCase):
    url = None
    fake = Faker()

    def setUp(self):
        super(ProductSubGroupDetailsAPITest,self).setUp()

        # set a product group
        self.admin_user_product_sub_group = ProductSubGroupFactory(
            organization=self.admin_user.organization)

        # set the url
        self.url = reverse('pharmacy.product.subgroup-details',
                           args=[self.admin_user_product_sub_group.alias])

    def test_product_sub_group_details_get(self):
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
            request.data['id'], self.admin_user_product_sub_group.id)

        # admin user logout
        self.client.logout()

    def test_product_sub_group_details_put(self):
        data = {
            'name': self.fake.first_name(),
            'description': self.fake.text(),
            'product_group': ProductGroupFactory().pk
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
        self.assertEqual(request.data['product_group'], data['product_group'])

        # admin user logout
        self.client.logout()


        def test_product_sub_group_details_delete(self):
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
            self.assertEqual(ProductSubgroup.objects.count(), 1)
            request = self.client.delete(self.url)
            self.assertDeleted(request)

            # admin user logout
            self.client.logout()


# class ProductSubGroupSearchAPITest(OmisTestCase):
#     url = reverse('pharmacy.product.subgroup-search')
#     fake = Faker()

#     def setUp(self):
#         super(ProductSubGroupSearchAPITest, self).setUp()

#     def test_product_sub_group_list_get(self):
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
#         ProductSubGroupFactory(name="COG", organization=self.admin_user.organization)
#         d1 = ProductSubGroupFactory(name="COJ")
#         d2 = ProductSubGroupFactory(name="COZ")


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
