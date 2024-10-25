from faker import Faker
from django.urls import reverse
from common.test_case import OmisTestCase
from pharmacy.tests import StorePointFactory, StockAdjustmentFactory
from core.tests import PatientFactory, EmployeeFactory
from common.enums import Status


class StockAdjustmentSearchAPITest(OmisTestCase):
    url = reverse('pharmacy.stock-adjustment-search')
    fake = Faker()

    # def setUp(self):
    #     super(StockAdjustmentSearchAPITest, self).setUp()

    def test_pharmacy_stock_adjustment_search_get(self):
        # Create a storepoint and a stock adjustment
        store_point = StorePointFactory(name=self.fake.first_name())
        patient = PatientFactory(
            first_name=self.fake.first_name(),
            last_name=self.fake.last_name(),
            status=Status.ACTIVE,
            organization=self.admin_user.organization)
        employee = EmployeeFactory(
            first_name=self.fake.first_name(),
            last_name=self.fake.last_name(),
            status=Status.ACTIVE,
            organization=self.admin_user.organization)
        stock_adjustment = StockAdjustmentFactory.create_batch(
            2,
            store_point=store_point,
            status=Status.ACTIVE,
            organization=self.admin_user.organization,
            is_product_disbrustment=False,
            patient=patient,
            employee=employee
        )

        # search data
        data1 = {
            'keyword': 'les',
        }

        data2 = {
            'keyword': str(store_point.name),
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check with first keyword
        self.assertEqual(request.data['count'], 0)

        # check with another keyword
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 2)

        # sort data by id
        request.data['results'] = sorted(
            request.data['results'], key=lambda id: id['id']
        )

        self.assertEqual(
            request.data['results'][0]['id'],
            stock_adjustment[0].id)
        self.assertEqual(
            request.data['results'][0]['alias'],
            str(stock_adjustment[0].alias))
        self.assertEqual(
            request.data['results'][0]['store_point']['name'],
            stock_adjustment[0].store_point.name)

        self.assertEqual(
            request.data['results'][1]['id'],
            stock_adjustment[1].id)
        self.assertEqual(
            request.data['results'][1]['alias'],
            str(stock_adjustment[1].alias))
        self.assertEqual(
            request.data['results'][1]['store_point']['name'],
            stock_adjustment[1].store_point.name)
