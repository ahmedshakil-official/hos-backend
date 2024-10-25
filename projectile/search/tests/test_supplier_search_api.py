# from django.urls import reverse
# from common.test_case import OmisTestCase
# from core.tests import SupplierFactory
# from common.enums import Status


# class SupplierSearchAPITest(OmisTestCase):
#     url = reverse('supplier-search')

#     # def setUp(self):
#     #     super(SupplierSearchAPITest, self).setUp()

#     def test_patient_list_search_get(self):
#         supplier = SupplierFactory.create_batch(
#             2, company_name='test',
#             organization=self.admin_user.organization,
#             status=Status.ACTIVE
#         )

#         # search data
#         data1 = {
#             'keyword': 'les',
#         }

#         data2 = {
#             'keyword': 'test',
#         }

#         # ===========================================
#         #  Check without login
#         # ===========================================
#         request = self.client.get(self.url, data1)
#         self.assertPermissionDenied(request)

#         # ===========================================
#         #  Check with login
#         # ===========================================
#         login = self.client.login(phone=self.user.phone, password='testpass')
#         self.assertTrue(login)
#         request = self.client.get(self.url, data1)
#         self.assertSuccess(request)

#         # ===========================================
#         #  Check for admin user
#         # ===========================================
#         login = self.client.login(
#             phone=self.admin_user.phone, password='testpass')
#         self.assertTrue(login)
#         request = self.client.get(self.url, data1)
#         self.assertSuccess(request)

#         # ===========================================
#         #  Check for admin user of the same organization
#         # ===========================================
#         request = self.client.get(self.url, data1)
#         self.assertSuccess(request)

#         # check with first keyword
#         self.assertEqual(request.data['count'], 0)

#         # check with another keyword
#         request = self.client.get(self.url, data2)
#         self.assertSuccess(request)

#         self.assertEqual(request.data['count'], 2)

#         supplier[0].delete()
#         request = self.client.get(self.url, data2)
#         self.assertSuccess(request)

#         self.assertEqual(request.data['count'], 1)


#         # logout
#         self.client.logout()
