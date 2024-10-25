from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status
from clinic.tests import DutyShiftFactory
from core.tests import EmployeeFactory
from core.models import PersonOrganization


class EmployeeDutyShiftSearchAPITest(OmisTestCase):
    url = reverse('employee-dutyshift-search')

    def test_employee_dutyshift_search_get(self):
        dutyshift = DutyShiftFactory(
            organization=self.admin_user.organization,
            status=Status.ACTIVE,
        )
        employee = EmployeeFactory(
            first_name="test", last_name="othe",
            status=Status.ACTIVE,
            organization=self.admin_user.organization
        )
        employee_organization = PersonOrganization.objects.get(person=employee)
        employee_organization.duty_shift = dutyshift
        employee_organization.save(update_fields=["duty_shift"])

        data1 = {
            'keyword': 'test'
        }

        data2 = {
            'keyword': 'z'
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)
        # check if it is the same user

        self.assertEqual(request.data['count'], 1)

        self.assertEqual(
            request.data['results'][0]['first_name'], employee.first_name
        )
        self.assertEqual(
            request.data['results'][0]['last_name'], employee.last_name
        )

        # check with another keywod
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 0)

        # logout
        self.client.logout()
