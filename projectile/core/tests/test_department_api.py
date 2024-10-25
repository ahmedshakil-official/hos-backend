import json
from faker import Faker

from django.urls import reverse

from common.utils import inactive_instance
from common.test_case import OmisTestCase
from core.tests import DepartmentFactory

from ..models import Department


class DepartmentListAPITest(OmisTestCase):
    url = reverse('department-list')
    fake = Faker()

    def setUp(self):
        super(DepartmentListAPITest, self).setUp()

    def test_department_list_get(self):
        department_will_be_deleted = DepartmentFactory.create_batch(
            2,
            organization=self.admin_user.organization
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
        # request = self.client.get(self.url)
        # self.assertSuccess(request)
        # # check if it is the same user
        # self.assertEqual(request.data['count'], 0)

        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        # self.admin_user.organization = self.user.organization
        # self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        department_will_be_deleted[0].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()

    def test_department_list_post(self):
        # ===========================================
        #  Check without login
        # ===========================================
        data = {
            'name': self.fake.first_name(),
            'description': self.fake.text()
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
        self.assertEqual(Department.objects.count(), 1)
        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['description'], data['description'])


class DepartmentSearchAPITest(OmisTestCase):
    url = reverse('department-search')
    fake = Faker()

    def setUp(self):
        super(DepartmentSearchAPITest, self).setUp()

    def test_department_list_get(self):
        # first create some persons
        d1 = DepartmentFactory(name="CEO")
        d2 = DepartmentFactory(name="CTO")

        # search data
        data = {
            'keyword': 'c'
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        # login = self.client.login(phone=self.user.phone, password='testpass')
        # self.assertTrue(login)
        # request = self.client.get(self.url, data)
        # self.assertPermissionDenied(request)

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
        d1.organization = self.admin_user.organization
        d1.save()
        d2.organization = self.admin_user.organization
        d2.save()

        request = self.client.get(self.url, data)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 2)

        inactive_instance(d1)

        request = self.client.get(self.url, data)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()


class DepartmentDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        # call the super
        super(DepartmentDetailsAPITest, self).setUp()
        # create a designation with the admin organization
        self.department = DepartmentFactory(
            organization=self.admin_user.organization
        )
        # reverse the url from name
        self.url = reverse('department-details', args=[self.department.alias])

    def test_department_details_get(self):
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
        # request = self.client.get(self.url)
        # self.assertPermissionDenied(request)

        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        # self.admin_user.organization = self.user.organization
        # self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)
        # check if it is the same instance
        self.assertEqual(request.data['id'], self.department.pk)

        # logout
        self.client.logout()

    def test_department_details_put(self):
        data = {
            'name': self.fake.first_name(),
            'description': self.fake.text()
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
        # request = self.client.put(self.url, data=json.dumps(
        #     dict(data)), content_type='application/json')
        # self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================
        # self.admin_user.organization = self.user.organization
        # self.admin_user.save()
        request = self.client.put(self.url, data=json.dumps(
            dict(data)), content_type='application/json')
        self.assertSuccess(request)
        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['description'], data['description'])

        # logout
        self.client.logout()

    def test_department_details_delete(self):
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
        request = self.client.delete(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone,
            password='testpass'
        )
        self.assertTrue(login)
        # request = self.client.delete(self.url)
        # self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================
        # self.admin_user.organization = self.user.organization
        # self.admin_user.save()
        request = self.client.delete(self.url)
        self.assertDeleted(request)

        # logout
        self.client.logout()
