# from faker import Faker

# from django.urls import reverse

# from common.test_case import OmisTestCase
# from pharmacy.tests import StockFactory, ProductFactory


# class StockListSearchAPITest(OmisTestCase):
#     url = reverse('pharmacy-stock-search')
#     fake = Faker()

#     # def setUp(self):
#     #     super(StockListSearchAPITest, self).setUp()

#     def test_stock_list_get(self):

#         stock = StockFactory.create_batch(
#             2,
#             product=ProductFactory(
#                 organization=self.admin_user.organization,
#                 name="test",
#                 is_service=False
#             ),
#             organization=self.admin_user.organization
#         )

#         # search data
#         data1 = {
#             'keyword': 'lest',
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
#         self.client.logout()

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
#         self.assertEqual(
#             request.data['results'][0]['id'],
#             stock[1].id)
#         self.assertEqual(
#             request.data['results'][0]['alias'],
#             str(stock[1].alias))
#         self.assertEqual(
#             request.data['results'][0]['store_point']['name'],
#             str(stock[1].store_point.name))
#         self.assertEqual(
#             request.data['results'][0]['product']['name'],
#             str(stock[1].product.name))

#         self.assertEqual(
#             request.data['results'][1]['id'],
#             stock[0].id)
#         self.assertEqual(
#             request.data['results'][1]['alias'],
#             str(stock[0].alias))
#         self.assertEqual(
#             request.data['results'][1]['store_point']['name'],
#             str(stock[0].store_point.name))
#         self.assertEqual(
#             request.data['results'][1]['product']['name'],
#             str(stock[0].product.name))

#         # logout
#         self.client.logout()
