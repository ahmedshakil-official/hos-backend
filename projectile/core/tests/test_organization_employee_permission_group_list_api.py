from django.urls import reverse
from common.test_case import OmisTestCase
from core.tests import PersonOrganizationGroupPermissionFactory
from ..models import PersonOrganization
from . import EmployeeFactory

class OrganizationEmployeePermissionGroupAPITest(OmisTestCase):
    def setUp(self):
        super(OrganizationEmployeePermissionGroupAPITest, self).setUp()

        # create an employee
        self.employee = EmployeeFactory(organization=self.user.organization)
        self.person_organization = PersonOrganization.objects.get(person=self.employee)

        # set the url
        self.person_organization_permission = PersonOrganizationGroupPermissionFactory(
            person_organization=self.person_organization)
        self.url = reverse('organization-employee-permission-group-list')

    def test_organization_employee_permission_get(self):
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
        data = {'employee_alias': self.employee.alias}
        request = self.client.get(self.url, data)
        self.assertSuccess(request)
        #Check if it is the same employee for the employee
        self.assertEqual(request.data['count'], 1)
        self.assertEqual(request.data['results'][0]['name'],
                         self.person_organization_permission.permission.name)

        # without params, requested as user
        request = self.client.get(self.url)
        self.assertSuccess(request)
        self.assertEqual(request.data['count'], 0)
        # admin user logout
        self.client.logout()
