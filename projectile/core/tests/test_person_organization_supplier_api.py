import json
import random
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from core.tests import PersonOrganizationSupplierFactory

from ..models import PersonOrganization
from ..enums import PersonGroupType


class PersonOrganizationSupplierListAPITest(OmisTestCase):
    url = reverse('person-organization-supplier-list')
    fake = Faker()

    # def setUp(self):
    #     super(PersonOrganizationSupplierListAPITest, self).setUp()

    def test_supplier_list_get(self):
        supplier = PersonOrganizationSupplierFactory.create_batch(
            2, organization=self.admin_user.organization)

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
        self.assertEqual(request.data['count'], 2)

        supplier[1].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)
        self.assertEqual(
            request.data['results'][0]['alias'],
            str(supplier[0].alias)
        )

        # logout
        self.client.logout()

    def test_supplier_list_post(self):
        # ===========================================
        #  Check without login
        # ===========================================
        data = {
            'phone': self.fake.msisdn(),
            'opening_balance': random.randint(0, 120),
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
        self.assertEqual(PersonOrganization.objects.filter(
            person_group=PersonGroupType.SUPPLIER).count(), 1)

        self.assertEqual(request.data['company_name'], data['company_name'])
        self.assertEqual(request.data['phone'], data['phone'])
        self.assertEqual(
            request.data['opening_balance'], data['opening_balance'])
        self.assertEqual(request.data['email'], data['email'])
        self.assertEqual(
            request.data['contact_person_number'],
            data['contact_person_number']
        )

        # logout
        self.client.logout()


class PersonOrganizationSupplierDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(PersonOrganizationSupplierDetailsAPITest, self).setUp()
        # create a designation
        self.supplier = PersonOrganizationSupplierFactory(organization=self.user.organization)

        self.url = reverse(
            'person-organization-supplier-details',
            args=[self.supplier.alias]
        )

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
        self.assertSuccess(request)

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        data['company_name'] = self.fake.company()
        request = self.client.put(self.url, data=json.dumps(
            dict(data)), content_type='application/json')
        self.assertSuccess(request)
        self.assertEqual(request.data['phone'], data['phone'])
        self.assertEqual(
            request.data['opening_balance'], data['opening_balance'])
        self.assertEqual(request.data['joining_date'], data['joining_date'])
        self.assertEqual(request.data['email'], data['email'])
        self.assertEqual(
            request.data['contact_person_number'],
            data['contact_person_number']
        )
        self.assertEqual(request.data['company_name'], data['company_name'])

        # logout
        self.client.logout()


class PersonOrganizationSupplierSearchAPITest(OmisTestCase):
    url = reverse('person-organization-supplier-search')
    fake = Faker()

    # def setUp(self):
    #     super(PersonOrganizationSupplierSearchAPITest, self).setUp()

    def test_supplier_search_list(self):
        # first create some persons
        supplier_1 = PersonOrganizationSupplierFactory(
            company_name="supplier1", phone="01557", email="b@ab.com")
        supplier_2 = PersonOrganizationSupplierFactory(
            company_name="supplier2", phone="01947", email="e@ab.com")

        # search data
        data = {
            'keyword': 'sup'
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data)
        self.assertSuccess(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 0)

        # ===============================================
        #  Check for admin user of the same organization
        # ===============================================
        supplier_1.organization = self.admin_user.organization
        supplier_1.save()
        supplier_2.organization = self.admin_user.organization
        supplier_2.save()

        request = self.client.get(self.url, data)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 2)

        # search data
        data = {
            'keyword': '01'
        }

        request = self.client.get(self.url, data)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 2)

        # search data
        data = {
            'keyword': '01947'
        }

        request = self.client.get(self.url, data)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 1)
        # search data
        data = {
            'keyword': '0155'
        }

        request = self.client.get(self.url, data)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 1)

        # search data
        data = {
            'keyword': '015589'
        }

        request = self.client.get(self.url, data)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 0)

        # search data
        data = {
            'keyword': '@ab.com'
        }

        request = self.client.get(self.url, data)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 2)

        # logout
        self.client.logout()
