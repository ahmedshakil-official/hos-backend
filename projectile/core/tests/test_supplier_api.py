import json
import random
from faker import Faker

from django.urls import reverse

from common.enums import Status
from common.utils import inactive_instance
from common.test_case import OmisTestCase
from core.tests import PersonFactory, SupplierFactory

from ..models import Person
from ..enums import PersonGroupType


class SupplierListAPITest(OmisTestCase):
    url = reverse('supplier-list')
    fake = Faker()

    def setUp(self):
        super(SupplierListAPITest, self).setUp()

    def test_supplier_list_get(self):
        supplier_will_be_deleted = SupplierFactory.create_batch(2, organization=self.user.organization)

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

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)
        # check if it is the same user
        self.assertEqual(request.data['count'], 0)

        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        inactive_instance(supplier_will_be_deleted[0])

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()

    def test_supplier_list_post(self):
        # ===========================================
        #  Check without login
        # ===========================================
        data = {
            'first_name': self.fake.first_name(),
            'last_name': self.fake.last_name(),
            'phone': self.fake.msisdn(),
            'opening_balance' : random.randint(0, 120),
            'contact_person_number': self.fake.msisdn(),
            'joining_date': self.fake.date(pattern="%Y-%m-%d"),
            'email': '{}@example.com'.format(self.fake.ssn()),
            'company_name': self.fake.company(),
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

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.post(self.url, data)
        self.assertCreated(request)
        self.assertEqual(Person.objects.filter(
            person_group=PersonGroupType.SUPPLIER).count(), 1)

        self.assertEqual(request.data['first_name'], data['first_name'])
        self.assertEqual(request.data['last_name'], data['last_name'])
        self.assertEqual(request.data['phone'], data['phone'])
        self.assertEqual(request.data['opening_balance'], data['opening_balance'])
        self.assertEqual(request.data['joining_date'], data['joining_date'])
        self.assertEqual(request.data['email'], data['email'])
        self.assertEqual(request.data['contact_person_number'], data['contact_person_number'])
        self.assertEqual(request.data['company_name'], data['company_name'])


class SupplierDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(SupplierDetailsAPITest, self).setUp()
        # create a designation
        self.supplier = SupplierFactory(organization=self.user.organization)

        self.url = reverse('supplier-details', args=[self.supplier.alias])

    def test_supplier_details_get(self):
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

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)
        # check if it is the same instance
        self.assertEqual(request.data['id'], self.supplier.pk)

        # logout
        self.client.logout()

    def test_supplier_details_put(self):
        data = {
            'phone': self.fake.msisdn(),
            'opening_balance': random.randint(0, 120),
            'contact_person_number': self.fake.msisdn(),
            'joining_date': self.fake.date(pattern="%Y-%m-%d"),
            'email': '{}@example.com'.format(self.fake.ssn()),
            'company_name': self.fake.company(),
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

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.put(self.url, data=json.dumps(
            dict(data)), content_type='application/json')
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.put(self.url, data=json.dumps(
            dict(data)), content_type='application/json')
        self.assertSuccess(request)
        self.assertEqual(request.data['phone'], data['phone'])
        self.assertEqual(request.data['opening_balance'], data['opening_balance'])
        self.assertEqual(request.data['joining_date'], data['joining_date'])
        self.assertEqual(request.data['email'], data['email'])
        self.assertEqual(request.data['contact_person_number'], data['contact_person_number'])
        self.assertEqual(request.data['company_name'], data['company_name'])

        # logout
        self.client.logout()

    def test_supplier_details_inactive(self):
        data = {
            'status': Status.INACTIVE,
        }
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.patch(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.patch(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.patch(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.patch(self.url, data=json.dumps(
            dict(data)), content_type='application/json')
        self.assertSuccess(request)

        request = self.client.get(self.url)
        self.assertNotFound(request)

        # logout
        self.client.logout()


# class SupplierSearchAPITest(OmisTestCase):
#     url = reverse('supplier-search')
#     fake = Faker()

#     def setUp(self):
#         super(SupplierSearchAPITest, self).setUp()

#     def test_supplier_list_get(self):
#         # first create some persons
#         d1 = SupplierFactory(first_name="CEO", last_name="A GM",
#                              phone="01557", email="b@b.com")
#         d2 = SupplierFactory(first_name="CTO", last_name="GM",
#                              phone="01947", email="a@b.com")

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
#         self.assertSuccess(request)

#         # ===========================================
#         #  Check for admin user
#         # ===========================================
#         login = self.client.login(
#             phone=self.admin_user.phone, password='testpass')
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
#         self.assertEqual(request.data['count'], 2)

#         # search data
#         data = {
#             'keyword': '01'
#         }

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 2)

#         # search data
#         data = {
#             'keyword': '01947'
#         }

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 1)
#         # search data
#         data = {
#             'keyword': '0155'
#         }

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 1)

#         # search data
#         data = {
#             'keyword': '015589'
#         }

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 0)

#         # search data
#         # data = {
#         #     'keyword': 'a@'
#         # }
#         #
#         # request = self.client.get(self.url, data)
#         # self.assertSuccess(request)

#         # check if it is the same instance
#         # self.assertEqual(request.data['count'], 1)
#         #
#         # # search data
#         # data = {
#         #     'keyword': 'b@'
#         # }
#         #
#         # request = self.client.get(self.url, data)
#         # self.assertSuccess(request)
#         #
#         # # check if it is the same instance
#         # self.assertEqual(request.data['count'], 1)

#         # search data
#         data = {
#             'keyword': '@b.com'
#         }

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 2)

#         # search data
#         data = {
#             'keyword': 'GM'
#         }

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 2)

#         # search data
#         data = {
#             'keyword': 'A GM'
#         }

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 1)

#         # search data
#         data = {
#             'keyword': 'A'
#         }

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 2)

#         d1.delete()

#         # search data
#         data = {
#             'keyword': 'c'
#         }

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 1)

#         # logout
#         self.client.logout()
