from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status
from common.utils import inactive_instance

from core.tests import (
    EmployeeFactory,
    PersonOrganizationGroupPermissionFactory, )
from pharmacy.models import EmployeeStorepointAccess
from pharmacy.tests import StorePointFactory


class StorePointSearchAPITest(OmisTestCase):
    url = reverse('pharmacy.storepoint.search')

    def setUp(self):
        super(StorePointSearchAPITest, self).setUp()

    def test_store_point_search_get(self):
        organization = self.employee_user.organization
        #create an store_point
        self.store_point = StorePointFactory(
            name='teststorepoint',
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

        store_point = StorePointFactory.create_batch(
            3,
            name='test',
            organization=self.admin_user.organization,
            status=Status.ACTIVE
        )

        data1 = {
            'keyword': 'nest'
        }

        data2 = {
            'keyword': 'test'
        }

        data3 = {
            'keyword': 'teststorepoint',
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
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check for store_points employee user
        # ===========================================
        login = self.client.login(
            phone=self.person_organization_employee.phone,
            password='testpass'
        )
        self.assertTrue(login)
        request = self.client.get(self.url, data3)
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
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check if data1 keyword returns zero search result
        self.assertEqual(request.data['count'], 0)

        # check with data2 keyword
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if data2 keyword returns three search result
        self.assertEqual(request.data['count'], 3)

        # inactive first entry
        inactive_instance(store_point[0])

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if it is now returns two result after deletion
        self.assertEqual(request.data['count'], 2)

        # logout
        self.client.logout()
