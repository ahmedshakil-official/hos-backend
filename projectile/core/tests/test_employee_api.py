import json
from faker import Faker

from django.urls import reverse

from common.enums import Status
from common.utils import inactive_instance
from common.test_case import OmisTestCase
from . import PersonFactory, EmployeeFactory, DesignationFactory

from ..enums import PersonGroupType, PersonGender
from ..models import Person


class EmployeeListAPITest(OmisTestCase):
    url = reverse('employee-list')
    fake = Faker()

    def setUp(self):
        super(EmployeeListAPITest, self).setUp()
        self.user = PersonFactory(person_group=PersonGroupType.SYSTEM_ADMIN)

    def test_employee_list_get(self):
        employee_will_be_deleted = EmployeeFactory.create_batch(
            2, organization=self.user.organization
        )

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

        inactive_instance(employee_will_be_deleted[0])

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()

    def test_employee_list_post(self):
        # ===========================================
        #  Check without login
        # ===========================================
        previous_count = Person.objects.filter(
            person_group=PersonGroupType.EMPLOYEE
        ).count()
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
        request = self.client.post(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        # login = self.client.login(phone=self.user.phone, password='testpass')
        # self.assertTrue(login)

        # request = self.client.post(self.url, data)
        # self.assertPermissionDenied(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.post(self.url, data)
        self.assertCreated(request)
        self.assertEqual(
            Person.objects.filter(
                person_group=PersonGroupType.EMPLOYEE
            ).count(), previous_count + 1
        )
        self.assertEqual(request.data['first_name'], data['first_name'])
        self.assertEqual(request.data['last_name'], data['last_name'])
        self.assertEqual(request.data['phone'], data['phone'])
        self.assertEqual(request.data['gender'], data['gender'])
        self.assertEqual(request.data['dob'], data['dob'])
        self.assertEqual(request.data['designation'], data['designation'])
        self.assertEqual(request.data['degree'], data['degree'])


class EmployeeDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(EmployeeDetailsAPITest, self).setUp()
        # create a designation
        self.patient = EmployeeFactory(organization=self.user.organization)

        self.url = reverse('employee-details', args=[self.patient.alias])

    def test_employee_details_get(self):
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
        self.assertEqual(request.data['id'], self.patient.pk)

        # logout
        self.client.logout()

    def test_employee_details_put(self):
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

    def test_employee_details_inactive(self):
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
