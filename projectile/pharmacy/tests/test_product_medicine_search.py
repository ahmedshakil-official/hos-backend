# from faker import Faker

# from django.urls import reverse

# from common.test_case import OmisTestCase

# from ..tests import ProductFactory, ProductGroupFactory, ProductSubGroupFactory


# class ProductMedicineSearchAPITest(OmisTestCase):
#     url = reverse('pharmacy.product.medicine.search')
#     fake = Faker()

#     def setUp(self):
#         super(ProductMedicineSearchAPITest,self).setUp()

#     def test_product_medicine_list_get(self):
#         # first create some persons
#         d1 = ProductFactory(name="CEO")
#         d2 = ProductFactory(name="CTO")
#         group = ProductGroupFactory(name="Medicine")
#         sub_group = ProductSubGroupFactory(product_group=group)

#         # search data
#         data = {
#             'keyword': 'c'
#         }

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

#         # check if it is the same user
#         self.assertEqual(request.data['count'], 0)

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
#         self.assertEqual(request.data['count'], 0)

#         # setting form equal medicine
#         d1.subgroup = sub_group
#         d2.subgroup = sub_group
#         d1.save()
#         d2.save()

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 2)

#         d1.delete()

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 1)

#         # logout
#         self.client.logout()
