# from faker import Faker
# from django.urls import reverse
# from common.test_case import OmisTestCase
# from . import EmployeeFactory, SupplierFactory


# class EmployeeSupplierSearchAPITest(OmisTestCase):
#     url = reverse('employee-supplier-search')
#     fake = Faker()

#     # def setUp(self):
#     #     super(EmployeeSupplierSearchAPITest, self).setUp()

#     def test_employee_supplier_list_get(self):
#         # first create employee and supplier
#         employee = EmployeeFactory(first_name=self.fake.first_name())
#         supplier = SupplierFactory(company_name=employee.first_name)

#         # search data
#         data = {
#             'keyword': str(employee.first_name)
#         }

#         data_2 = {
#             'keyword': 'ttt'
#         }

#         # ===========================================
#         #  Check without login
#         # ===========================================
#         request = self.client.get(self.url)
#         self.assertPermissionDenied(request)

#         # ===========================================
#         #  Check for admin user
#         # ===========================================
#         login = self.client.login(
#             phone=self.admin_user.phone, password='testpass')
#         self.assertTrue(login)

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 2)

#         employee.delete()

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 1)

#         # Check if request company name and supplier are same
#         self.assertEqual(request.data['results'][0]['company_name'], supplier.company_name)

#         # test with keyword that return none
#         request = self.client.get(self.url, data_2)
#         self.assertSuccess(request)

#         # check is it return 0 data
#         self.assertEqual(request.data['count'], 0)

#         # logout
#         self.client.logout()
