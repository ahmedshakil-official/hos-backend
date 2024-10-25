import random
import datetime
from datetime import datetime

from faker import Faker
from django.urls import reverse
from django.core.cache import cache

from common.enums import Status
from common.test_case import OmisTestCase

from pharmacy.models import EmployeeStorepointAccess
from pharmacy.tests import (
    StorePointFactory,
    ProductFactory,
    StockIOLogFactory,
    StockFactory,
    StockAdjustmentFactory,
    StockTransferFactory, )

from pharmacy.enums import InventoryType, StockIOType


# class InventorySummaryAPITest(OmisTestCase):
#     url = reverse('pharmacy.inventory-summary-report')
#     fake = Faker()

#     def setUp(self):
#         super(InventorySummaryAPITest, self).setUp()
#         self.employee_user.is_staff = False
#         self.employee_user.save()


#     def test_inventory_summary_list_get(self):
#         date_time = datetime.now()
#         date = date_time.strftime('%Y-%m-%d')
#         organization = self.person_organization_employee.organization

#         # ====================== Entry for employee and admin ==============

#         # Create store points
#         store_points = StorePointFactory.create_batch(
#             2, organization=organization
#         )
#         store_points_list = [str(store.alias) for store in store_points]
#         store_points_alias = ','.join(store_points_list)
#         # Filtered Non-admin user and provided store point access
#         EmployeeStorepointAccess.objects.filter(
#             employee=self.employee_user
#         ).update(access_status=True)

#         # Create Product
#         product = ProductFactory(organization=organization)

#         io_logs_with_adjustment = []
#         io_logs_with_transfer = []

#         # Create employee Stock IO Log for multiple store-points
#         for store_point in store_points:
#             stock = StockFactory(
#                 product=product,
#                 organization=organization,
#                 status=Status.ACTIVE,
#                 store_point=store_point
#             )
#             stock_adjustment = StockAdjustmentFactory(
#                 organization=organization,
#                 date=date,
#                 store_point=store_point,
#                 is_product_disbrustment=False,
#             )
#             stock_transfer = StockTransferFactory(
#                 organization=organization,
#                 date=date,
#             )
#             quantity = random.randint(1, 5)
#             io_log_with_adjustment = StockIOLogFactory(
#                 stock=stock,
#                 organization=organization,
#                 quantity=quantity,
#                 date=date,
#                 adjustment=stock_adjustment,
#                 type=StockIOType.INPUT
#             )
#             quantity = random.randint(1, 5)
#             io_log_with_transfer = StockIOLogFactory(
#                 stock=stock,
#                 organization=organization,
#                 quantity=quantity,
#                 date=date,
#                 transfer=stock_transfer,
#                 type=StockIOType.INPUT
#             )
#             io_logs_with_adjustment.append(io_log_with_adjustment)
#             io_logs_with_transfer.append(io_log_with_transfer)

#         # Sorted Stock Io log data based on date and store_point name
#         io_logs_with_adjustment = sorted(
#             io_logs_with_adjustment, key=lambda io_log_with_adjustment: (
#                 io_log_with_adjustment.stock.store_point.name,
#                 io_log_with_adjustment.date
#                 )
#             )
#         io_logs_with_transfer = sorted(
#             io_logs_with_transfer, key=lambda io_log_with_transfer: (
#                 io_log_with_transfer.stock.store_point.name,
#                 io_log_with_transfer.date
#                 )
#             )
#         # params for employee user
#         data = {
#             'date_0': date,
#             'date_1': date,
#             'store_points': store_points_alias,
#             'product': str(stock.product.alias),
#             'inventory_type' : random.choice(
#                 [InventoryType.ADJUSTMENT_IN, InventoryType.TRANSFER_IN]
#             )
#         }

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
#         # user logout
#         self.client.logout()

#         # # ===========================================
#         # #  Check for admin user
#         # # ===========================================
#         login = self.client.login(phone=self.admin_user.phone, password='testpass')
#         self.assertTrue(login)
#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)
#         # admin logout
#         self.client.logout()

#         # ===========================================
#         #  Employee Check with login
#         # ===========================================
#         login = self.client.login(
#             phone=self.person_organization_employee.phone,
#             password='testpass'
#         )
#         self.assertTrue(login)

#         # Set Person Organization Group Permission
#         self.employee_group_permission.permission = self.procurement_group
#         self.employee_group_permission.save()

#         # expire permission cache for current user
#         key_name = self.person_organization_employee.get_permission_cache_key(
#             EmployeeStorepointAccess
#         )
#         self.person_organization_employee.cache_expire(key_name)

#         # Check request with Procurement Permission
#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)
#         # Compare request data with IO logs using Stock adjustment and Stock Transfer
#         # based on parameter inventory_type
#         # Check when inventory type is ADJUSTMENT IN
#         if data['inventory_type'] == InventoryType.ADJUSTMENT_IN:
#             self.assertEqual(
#                 request.data[0]['store_point'],
#                 io_logs_with_adjustment[0].stock.store_point.name
#             )
#             self.assertEqual(
#                 request.data[0]['quantity'],
#                 io_logs_with_adjustment[0].quantity
#             )
#             self.assertEqual(
#                 request.data[1]['store_point'],
#                 io_logs_with_adjustment[1].stock.store_point.name
#             )
#             self.assertEqual(
#                 request.data[1]['quantity'],
#                 io_logs_with_adjustment[1].quantity
#             )

#         # Check when inventory type is TRANSFER IN
#         if data['inventory_type'] == InventoryType.TRANSFER_IN:
#             print(request.data, 'request.data')
#             self.assertEqual(
#                 request.data[0]['store_point'],
#                 io_logs_with_transfer[0].stock.store_point.name
#             )
#             self.assertEqual(request.data[0]['quantity'], io_logs_with_transfer[0].quantity)
#             self.assertEqual(
#                 request.data[1]['store_point'],
#                 io_logs_with_transfer[1].stock.store_point.name
#             )
#             self.assertEqual(request.data[1]['quantity'], io_logs_with_transfer[1].quantity)
#         self.client.logout()

#         # # ===========================================
#         # #  Check employee user when disabled storepoints access
#         # # ===========================================
#         login = self.client.login(phone=self.employee_user.phone, password='testpass')
#         self.assertTrue(login)
#         # expire cache first as it takes time for celery when expiring from signal
#         cache_key = self.person_organization_employee.get_permission_cache_key(
#             EmployeeStorepointAccess
#         )
#         cache.delete(cache_key)
#         # update user access
#         for item in EmployeeStorepointAccess.objects.filter(employee=self.employee_user):
#             item.access_status = False
#             item.save(update_fields=['access_status'])
#         # pass employee user data as params
#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)
#         # as all storepoints has no permission so data will be empty
#         self.assertEqual(len(request.data), 0)
#         # employee user logout
#         self.client.logout()
