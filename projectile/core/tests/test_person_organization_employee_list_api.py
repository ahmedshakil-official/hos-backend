from django.urls import reverse

from common.utils import inactive_instance
from common.test_case import OmisTestCase
from . import EmployeeFactory
from core.enums import PersonGroupType


class PersonOrganizationEmployeeListAPITest(OmisTestCase):
    url = reverse('person-organization-employee-list')

    def setUp(self):
        super(PersonOrganizationEmployeeListAPITest, self).setUp()

    def test_person_organization_employee_list_get(self):
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
        login = self.client.login(
            phone=self.admin_user.phone,
            password='testpass'
        )
        self.assertTrue(login)

        person = EmployeeFactory.create_batch(
            2,
            organization=self.admin_user.organization,
            person_group=PersonGroupType.EMPLOYEE
        )

        request = self.client.get(self.url)
        self.assertSuccess(request)

        self.assertEqual(request.data['results'][0]['first_name'], person[1].first_name)
        self.assertEqual(request.data['results'][0]['last_name'], person[1].last_name)
        self.assertEqual(request.data['results'][0]['phone'], person[1].phone)

        self.assertEqual(request.data['count'], 2)

        inactive_instance(person[0])

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        # create a person with another organization
        EmployeeFactory()

        # if organization is not created then query data will be same as before
        self.assertEqual(request.data['count'], 2)

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # now create with organization
        EmployeeFactory(organization=self.admin_user.organization)
        request = self.client.get(self.url)

        # Now query return exact number of data
        self.assertEqual(request.data['count'], 3)

        # admin user logout
        self.client.logout()
