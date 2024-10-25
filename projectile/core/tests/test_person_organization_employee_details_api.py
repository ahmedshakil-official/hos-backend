import json
from faker import Faker

from django.urls import reverse

from common.enums import Status
from common.test_case import OmisTestCase
from ..enums import PersonGender
from ..tests import PersonOrganizationEmployeeFactory, DesignationFactory
from ..models import PersonOrganization


class PersonOrganizationEmployeeDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(PersonOrganizationEmployeeDetailsAPITest, self).setUp()
        # create a person_organization employee instance
        self.employee = PersonOrganizationEmployeeFactory(organization=self.user.organization)

        self.url = reverse('person-organization-employee-details', args=[self.employee.alias])

    def test_person_organization_employee_details_get(self):
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
        # check if the entry is same as in database
        person_organization = PersonOrganization.objects.get(pk=self.employee.pk)
        self.assertEqual(person_organization.id, self.employee.pk)

        # check person entry with the coresponding person-organization
        self.assertEqual(person_organization.person.id, self.employee.person.pk)
        # check if it is the same instance
        self.assertEqual(request.data['id'], self.employee.pk)

        # logout
        self.client.logout()

    def test_person_organization_employee_details_put(self):
        # create an another designation
        designation = DesignationFactory(organization=self.user.organization)
        password = "{}{}".format(self.fake.first_name(), self.fake.msisdn())

        data = {
            'first_name': self.fake.first_name(),
            'last_name': self.fake.last_name(),
            'phone': self.fake.msisdn(),
            'gender': PersonGender.MALE,
            'dob': self.fake.date(pattern="%Y-%m-%d"),
            'designation': designation.id,
            'degree': self.fake.job(),
            'password': password,
            'confirm_password': password
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
        self.assertEqual(request.data['first_name'], data['first_name'])
        self.assertEqual(request.data['last_name'], data['last_name'])
        self.assertEqual(request.data['phone'], data['phone'])
        self.assertEqual(request.data['gender'], data['gender'])
        self.assertEqual(request.data['dob'], data['dob'])
        self.assertEqual(request.data['designation'], data['designation'])
        self.assertEqual(request.data['degree'], data['degree'])

        # logout
        self.client.logout()

    def test_person_organization_employee_details_delete(self):
        """
        patch request with status=INACTIVE and check if it works as same as DELETE
        without deleting content or data
        """
        data = {
            'status': Status.INACTIVE,
        }
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.delete(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.patch(self.url, data=json.dumps(
            dict(data)), content_type='application/json')
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.patch(self.url, data=json.dumps(
            dict(data)), content_type='application/json')
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.patch(self.url, data=json.dumps(
            dict(data)), content_type='application/json')

        # this will return data with status code 200, because data hasn't
        # deleted permanently, only status changed
        self.assertSuccess(request)

        # again perfor get request wih same alias of employee person-organization
        # it will return empty result with 404 not found status code
        request = self.client.get(self.url)
        self.assertNotFound(request)

        # logout
        self.client.logout()
