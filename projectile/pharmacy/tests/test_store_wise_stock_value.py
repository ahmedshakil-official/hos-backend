# import random
# from faker import Faker
# from django.urls import reverse

# from common.test_case import OmisTestCase

# from core.enums import PriceType
# from pharmacy.models import Stock
# from ..tests import StorePointFactory, StockIOLogFactory, ProductFactory
# from ..enums import StockIOType


# class StorePointWiseStockValueAPITest(OmisTestCase):
#     fake = Faker()
#     url = None

#     def setUp(self):
#         super(StorePointWiseStockValueAPITest, self).setUp()

#         self.store_point = StorePointFactory(
#             organization=self.admin_user.organization)

#         # set the url
#         self.url = reverse('pharmacy.store-wise-stock-value', args=[self.store_point.alias])

#     def test_store_wise_stock_value_list(self):
#         product = ProductFactory(
#             organization=self.admin_user.organization,
#             is_service=False
#         )
#         stock = Stock.objects.get(store_point=self.store_point)
#         stock.store_point = self.store_point
#         stock.calculated_price = product.purchase_price
#         stock.save()

#         price_types = [
#             PriceType.LATEST_PRICE,
#             PriceType.PRODUCT_PRICE,
#             PriceType.LATEST_PRICE_AND_PRODUCT_PRICE,
#             PriceType.PRODUCT_PRICE_AND_LATEST_PRICE
#         ]
#         self.admin_user.organization.organizationsetting.price_type = \
#             random.choice(price_types)

#         self.admin_user.organization.organizationsetting.save()

#         StockIOLogFactory.create_batch(
#             5,
#             batch='N/A',
#             organization=self.admin_user.organization,
#             stock=stock,
#             quantity=random.randint(100, 300),
#             type=StockIOType.INPUT
#         )
#         StockIOLogFactory.create_batch(
#             2,
#             batch='N/A',
#             organization=self.admin_user.organization,
#             stock=stock,
#             quantity=random.randint(1, 50),
#             type=StockIOType.OUT
#         )

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

#         # ===========================================
#         #  Check with admin user
#         # ===========================================
#         login = self.client.login(phone=self.admin_user.phone, password='testpass')
#         self.assertTrue(login)
#         request = self.client.get(self.url)
#         self.assertSuccess(request)

#         updated_stock = Stock.objects.get(store_point=self.store_point)
#         stock_value = updated_stock.stock * updated_stock.calculated_price
#         self.assertEqual(
#             request.data['results'][0]['stock_value'], stock_value
#         )

#         # admin user logout
#         self.client.logout()
