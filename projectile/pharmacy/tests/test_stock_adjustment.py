import json
import random
from faker import Faker
from django.urls import reverse
from common.test_case import OmisTestCase
from common.enums import Status
from pharmacy.enums import StockIOType
from core.tests import EmployeeFactory, PatientFactory
from clinic.tests import PatientAdmissionFactory
from ..tests import (
    StorePointFactory,
    StockAdjustmentFactory,
    StockIOLogFactory,
    StockFactory,
)
from ..models import StockAdjustment


class StockAdjustmentListApiTest(OmisTestCase):
    url = reverse('pharmacy.stock-adjustments')
    fake = Faker()

    def setUp(self):
        super(StockAdjustmentListApiTest, self).setUp()

    def test_stock_adjustment_list_get(self):
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

        stock_will_be_deleted = StockAdjustmentFactory.create_batch(
            2,
            organization=self.admin_user.organization,
            is_product_disbrustment=False
        )

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        stock_will_be_deleted[0].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        StockAdjustmentFactory()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # admin user logout
        self.client.logout()


    def test_stock_adjustment_list_post(self):
        # ===========================================
        #  Check without login
        # ===========================================
        # stock collect from stockFactory
        store_point = StorePointFactory(organization=self.admin_user.organization)
        employee = EmployeeFactory(organization=self.admin_user.organization)
        patient = PatientFactory(organization=self.admin_user.organization)
        patient_admission = PatientAdmissionFactory()
        person_organization_employee = employee.person_organization.get(
            organization=self.admin_user.organization,
            person_group=employee.person_group
        ).id
        stock = StockFactory(
            organization=self.admin_user.organization,
            stock=random.randint(1000, 2000),
            minimum_stock=random.randint(1000, 2000),
            auto_adjustment=random.choice([True, False]),
        )

        in_stock_io_log = StockIOLogFactory(
            organization=self.admin_user.organization,
            stock=stock,
            type=StockIOType.INPUT,
            batch='AAA',
            quantity=random.randint(5, 10)
        )
        in_stock_io_log2 = StockIOLogFactory(
            organization=self.admin_user.organization,
            stock=stock,
            type=StockIOType.INPUT,
            batch='BBB',
            quantity=random.randint(5, 10)
        )
        out_stock_io_log = StockIOLogFactory(
            organization=self.admin_user.organization,
            stock=stock,
            type=StockIOType.OUT,
            batch='AAA',
            quantity=random.randint(1, 5)
        )
        out_stock_io_log2 = StockIOLogFactory(
            organization=self.admin_user.organization,
            stock=stock,
            type=StockIOType.OUT,
            batch='BBB',
            quantity=random.randint(1, 5)
        )

        data = {
            "date": self.fake.date(),
            "store_point": store_point.pk,
            "employee": employee.pk,
            "person_organization_employee": person_organization_employee,
            "patient": patient.pk,
            "patient_admission": patient_admission.pk,
            "is_product_disbrustment": random.choice([True, False]),
            "remarks": self.fake.text(128),
            "stock_io_logs": [
                {
                    'stock': stock.pk,
                    'batch': in_stock_io_log.batch,
                    'type': in_stock_io_log.type,
                    'quantity': in_stock_io_log.quantity
                },
                {
                    'stock': stock.pk,
                    'batch': in_stock_io_log2.batch,
                    'type': in_stock_io_log2.type,
                    'quantity': in_stock_io_log2.quantity
                },
                {
                    'stock': stock.pk,
                    'batch': out_stock_io_log.batch,
                    'type': out_stock_io_log.type,
                    'quantity': out_stock_io_log.quantity
                },
                {
                    'stock': stock.pk,
                    'batch': out_stock_io_log2.batch,
                    'type': out_stock_io_log2.type,
                    'quantity': out_stock_io_log2.quantity
                }
            ]
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
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        previous_count = StockAdjustment.objects.count()
        request = self.client.post(self.url, data=json.dumps(
            dict(data)), content_type='application/json')
        self.assertCreated(request)
        self.assertEqual(StockAdjustment.objects.count(), previous_count + 1)
        self.assertEqual(request.data['date'], data['date'])
        self.assertEqual(request.data['store_point'], data['store_point'])
        self.assertEqual(
            request.data['person_organization_employee'], data['person_organization_employee'])
        self.assertEqual(request.data['patient'], data['patient'])
        self.assertEqual(
            request.data['patient_admission'], data['patient_admission'])
        self.assertEqual(
            request.data['is_product_disbrustment'], data['is_product_disbrustment'])
        self.assertEqual(request.data['remarks'], data['remarks'])


class StockAdjustmentDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(StockAdjustmentDetailsAPITest, self).setUp()

        # set a product
        self.stock_adjustment = StockAdjustmentFactory(organization=self.user.organization)

        # set the url
        self.url = reverse('pharmacy.stock-adjustment.details', args=[self.stock_adjustment.alias])


    def test_stock_adjustment_details_get(self):
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
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)
        self.assertEqual(request.data['id'], self.stock_adjustment.id)

        # admin user logout
        self.client.logout()

    def test_stock_adjustment_details_put(self):
        data = {
            "date": self.fake.date(),
            "store_point": StorePointFactory().pk,
            "employee": EmployeeFactory().pk,
            "patient": PatientFactory().pk,
            "patient_admission": PatientAdmissionFactory().pk,
            "is_product_disbrustment": random.choice([True, False]),
            "remarks": self.fake.text(128)
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
        request = self.client.put(self.url, data=json.dumps(dict(data)),
                                  content_type='application/json')
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.put(self.url, data=json.dumps(dict(data)),
                                  content_type='application/json')
        self.assertSuccess(request)

        self.assertEqual(request.data['patient'], data['patient'])
        self.assertEqual(request.data['employee'], data['employee'])
        self.assertEqual(request.data['store_point'], data['store_point'])
        self.assertEqual(request.data['patient_admission'], data['patient_admission'])
        self.assertEqual(request.data['is_product_disbrustment'], data['is_product_disbrustment'])
        self.assertEqual(request.data['remarks'], data['remarks'])


    def test_stock_adjustment_details_delete(self):
        data = {
            "status": Status.INACTIVE,
        }
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.patch(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.patch(self.url)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.patch(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        previous_count = StockAdjustment.objects.filter(status=Status.ACTIVE).count()
        request = self.client.patch(self.url, data)
        self.assertSuccess(request)
        self.assertEqual(
            StockAdjustment.objects.filter(status=Status.ACTIVE).count(), previous_count - 1)

        # admin user logout
        self.client.logout()
