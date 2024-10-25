from django.urls import reverse

from common.test_case import OmisTestCase

from pharmacy.tests import EmployeeStorepointAccessFactory, StorePointFactory
from core.tests import EmployeeFactory

class EmployeeStorePointAccessAPITest(OmisTestCase):
    url = reverse('pharmacy.employee-storepoint-access.list')

    def setUp(self):
        super(EmployeeStorePointAccessAPITest, self).setUp()

    def test_employee_store_point_access_list_get(self):
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

        employee_store_point_access = EmployeeStorepointAccessFactory.create_batch(
            2, organization=self.admin_user.organization
        )

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        employee_store_point_access[0].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # admin user logout
        self.client.logout()

    def test_employee_store_point_access_list_post(self):
        employee = EmployeeFactory()
        data = {
            "employee": employee.pk,
            "person_organization": employee.get_person_organization_for_employee().id,
            "store_point": StorePointFactory().pk,
            "organization": self.user.organization.pk,
            "access_status": True
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
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        # request = self.client.post(self.url, data)

        # self.assertCreated(request)
        # self.assertEqual(request.data['employee'], data['employee'])
        # self.assertEqual(request.data['store_point'], data['store_point'])
        # self.assertEqual(request.data['access_status'], data['access_status'])
        # self.assertEqual(EmployeeStorepointAccess.objects.count(), 1)
        # employee_store_point_access = EmployeeStorepointAccess.objects.get(pk=request.data['id'])
        # self.assertEqual(employee_store_point_access.organization, self.admin_user.organization)

        # admin user logout
        self.client.logout()


class EmployeeStorePointListAccessAPITest(OmisTestCase):

    url = reverse('pharmacy.employee-storepoint-access.list')
    def setUp(self):
        super(EmployeeStorePointListAccessAPITest, self).setUp()

    def test_employee_store_point_access_list(self):
        employee = EmployeeFactory()

        data = {
            "employee": employee.pk,
            "person_organization": employee.get_person_organization_for_employee().id,
            "store_point": StorePointFactory().pk,
            "organization": self.user.organization.pk,
            "access_status": True
        }

        url_to_get_employee_storepoint_list = reverse(
            'pharmacy.employee-storepoint.list', args=[employee.alias]
        )
        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.post(self.url, data)
        self.assertCreated(request)

        request_to_get_employee_storepoint_list = self.client.get(
            url_to_get_employee_storepoint_list
        )
        self.assertSuccess(request_to_get_employee_storepoint_list)

        self.assertEqual(
            request_to_get_employee_storepoint_list.data['results'][0]['employee']['id'],
            data['employee']
        )

        # admin user logout
        self.client.logout()
