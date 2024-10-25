import random
import json
from faker import Faker

from django.urls import reverse

from common.enums import Status
from common.utils import inactive_instance
from common.test_case import OmisTestCase

from core.tests import (
    EmployeeFactory,
    PersonOrganizationGroupPermissionFactory, )

from pharmacy.models import StorePoint, EmployeeStorepointAccess
from pharmacy.tests import StorePointFactory

class StorePointListsAPITest(OmisTestCase):
    url = reverse('pharmacy.storepoint.list')
    fake = Faker()

    def setUp(self):
        super(StorePointListsAPITest,self).setUp()

    def test_store_point_list_get(self):
        organization = self.employee_user.organization
        #create a store_point
        self.store_point = StorePointFactory(
            organization=organization
        )
        # Person Organization Group Permission
        salesman_group_permission = PersonOrganizationGroupPermissionFactory(
            person_organization=self.person_organization_employee,
            permission=self.salesman_group
        )
        procurement_group_permission = PersonOrganizationGroupPermissionFactory(
            person_organization=self.person_organization_employee,
            permission=self.procurement_group
        )
        nurse_group_permission = PersonOrganizationGroupPermissionFactory(
            person_organization=self.person_organization_employee,
            permission=self.nurse_group
        )

        #update employee access status
        employee_store_point_access = EmployeeStorepointAccess.objects.get(employee=self.employee_user)
        employee_store_point_access.access_status = True
        employee_store_point_access.save()

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
        #  store_points Employee Check with login
        # ===========================================
        login = self.client.login(
            phone=self.person_organization_employee.phone,
            password='testpass'
        )
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)
        self.assertEqual(request.data['count'], 1)
        self.assertEqual(
            request.data['results'][0]['id'],
            employee_store_point_access.store_point.id
        )
        self.assertEqual(
            request.data['results'][0]['name'],
            employee_store_point_access.store_point.name
        )
        self.assertEqual(
            request.data['results'][0]['type'],
            employee_store_point_access.store_point.type
        )
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        store_point_will_be_deleted = StorePointFactory.create_batch(
            2, organization=self.admin_user.organization,
            entry_by=EmployeeFactory(organization=self.admin_user.organization),
        )

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        inactive_instance(store_point_will_be_deleted[0])

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        StorePointFactory()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        StorePointFactory(organization=self.admin_user.organization)
        request = self.client.get(self.url)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        # admin user logout
        self.client.logout()

    def test_store_point_list_post(self):
        #data = factory.build(dict, FACTORY_CLASS=StorePointFactory)
        data = {
            'name': self.fake.company(),
            'phone': self.fake.msisdn(),
            'address': self.fake.address(),
            'auto_adjustment': random.choice([True, False]),
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
        #  store_points Employee Check with login
        # ===========================================
        login = self.client.login(
            phone=self.person_organization_employee.phone,
            password='testpass'
        )
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # user logout
        self.client.logout()
        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.post(self.url, data)
        store_point = StorePoint.objects.get(pk=request.data['id'])

        self.assertCreated(request)
        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['phone'], data['phone'])
        self.assertEqual(request.data['address'], data['address'])
        self.assertEqual(StorePoint.objects.count(), 1)
        self.assertEqual(store_point.organization, self.admin_user.organization)

        # admin user logout
        self.client.logout()


class StorePointDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(StorePointDetailsAPITest,self).setUp()

        self.store_point = StorePointFactory(organization=self.admin_user.organization)
        self.details_url = reverse('pharmacy.storepoint.details', args=[self.store_point.alias])

    def test_store_point_details_get(self):
        #############################################################################################
        # Testing if details cant be fetched without logging in
        #############################################################################################
        request = self.client.get(self.details_url)
        self.assertPermissionDenied(request)

        #############################################################################################
        # Testing if details cant be fetched by logging in but not as linked with storepoint
        #############################################################################################

        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.get(self.details_url)
        self.assertPermissionDenied(request)

        #############################################################################################
        # Logging out
        #############################################################################################

        self.client.logout()

        #############################################################################################
        # Testing if details cant be fetched by logging in as linked with storepoint
        #############################################################################################

        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.get(self.details_url)

        self.assertSuccess(request)

    def test_store_point_details_put(self):
        info = {
            'name': self.fake.company(),
            'phone': self.fake.msisdn(),
            'address': self.fake.address(),
            'auto_adjustment': random.choice([True, False]),
        }
        data = json.dumps(info, default=lambda data: data.__dict__)

        #############################################################################################
        # Testing without logging in
        #############################################################################################

        request = self.client.put(self.details_url, data, content_type="application/json")
        self.assertPermissionDenied(request)

        #############################################################################################
        # Testing  by logging in but not as linked with storepoint
        #############################################################################################

        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.put(self.details_url, data, content_type="application/json")
        self.assertPermissionDenied(request)
        self.client.logout()

        #############################################################################################
        # Testing  by logging in but not as linked with storepoint
        #############################################################################################

        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.put(self.details_url, data, content_type="application/json")
        self.assertSuccess(request)
        self.assertEqual(request.data['name'], info['name'])
        self.assertEqual(request.data['phone'], info['phone'])
        self.assertEqual(request.data['address'], info['address'])
        self.assertEqual(request.data['auto_adjustment'], info['auto_adjustment'])
        self.client.logout()

    def test_store_point_details_inactive(self):
        data = {
            'status': Status.INACTIVE,
        }
        #############################################################################################
        # Testing without logging in
        #############################################################################################
        request = self.client.patch(self.details_url, data)
        self.assertPermissionDenied(request)

        #############################################################################################
        # Testing  by logging in but not as linked with storepoint
        #############################################################################################

        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.patch(self.details_url, data)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        #############################################################################################
        # Testing  by logging in but not as linked with storepoint
        #############################################################################################
        self.admin_user.is_superuser = False
        self.admin_user.save()

        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.patch(self.details_url, data=json.dumps(
            dict(data)), content_type='application/json')
        # return bad request because only superuser now can inactive a storepoint
        self.assertBadRequest(request)

        # privilege as superuser
        self.admin_user.is_superuser = True
        self.admin_user.save()

        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)

        request = self.client.patch(self.details_url, data=json.dumps(
            dict(data)), content_type='application/json')
        self.assertSuccess(request)

        request = self.client.get(self.details_url)
        self.assertNotFound(request)

        self.client.logout()
