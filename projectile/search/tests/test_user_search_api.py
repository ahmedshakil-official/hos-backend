# from django.urls import reverse
# from common.test_case import OmisTestCase
# from core.tests import EmployeeFactory


# class UserSearchAPITest(OmisTestCase):
#     url = reverse('user-search')

#     # def setUp(self):
#     #     super(UserSearchAPITest, self).setUp()

#     def test_user_search_get(self):
#         person = EmployeeFactory.create_batch(
#             2, email='test@test.test',
#             organization=self.admin_user.organization
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
#         self.assertEqual(
#             request.data['results'][0]['first_name'],
#             person[1].first_name)
#         self.assertEqual(
#             request.data['results'][0]['last_name'],
#             person[1].last_name)
#         self.assertEqual(
#             request.data['results'][0]['email'],
#             person[1].email)

#         self.assertEqual(
#             request.data['results'][1]['first_name'],
#             person[0].first_name)
#         self.assertEqual(
#             request.data['results'][1]['last_name'],
#             person[0].last_name)
#         self.assertEqual(
#             request.data['results'][1]['email'],
#             person[0].email)

#         # logout
#         self.client.logout()
