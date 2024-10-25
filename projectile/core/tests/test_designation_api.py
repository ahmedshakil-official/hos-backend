import json
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from core.tests import PersonFactory, DesignationFactory, DepartmentFactory

from ..models import EmployeeDesignation


class DesignationListAPITest(OmisTestCase):
    url = reverse('designation-list')
    fake = Faker()

    def setUp(self):
        super(DesignationListAPITest, self).setUp()

    def test_designation_list_get(self):
        designation_will_be_deleted = DesignationFactory.create_batch(
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

        designation_will_be_deleted[0].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()

    def test_designation_list_post(self):
        # ===========================================
        #  Check without login
        # ===========================================
        data = {
            'name': self.fake.first_name(),
            'department': DepartmentFactory().pk,
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
        self.assertEqual(EmployeeDesignation.objects.count(), 1)

        self.assertEqual(request.data['name'], data['name'])
        self.assertEqual(request.data['department'], data['department'])
        self.assertEqual(request.data['description'], data['description'])


# class DesignationSearchAPITest(OmisTestCase):
#     url = reverse('designation-search')
#     fake = Faker()

#     def setUp(self):
#         super(DesignationSearchAPITest, self).setUp()

#     def test_designation_list_get(self):
#         # first create some persons
#         d1 = DesignationFactory(name="CEO", organization=self.admin_user.organization)
#         d2 = DesignationFactory(name="CTO", organization=self.admin_user.organization)

#         # search data
#         data = {
#             'keyword': 'c'
#         }

#         # ===========================================
#         #  Check without login
#         # ===========================================
#         request = self.client.get(self.url, data)
#         self.assertPermissionDenied(request)

#         # ===========================================
#         #  Check with login
#         # ===========================================
#         # login = self.client.login(phone=self.user.phone, password='testpass')
#         # self.assertTrue(login)
#         # request = self.client.get(self.url, data)
#         # self.assertPermissionDenied(request)

#         # ===========================================
#         #  Check for admin user
#         # ===========================================
#         login = self.client.login(
#             phone=self.admin_user.phone, password='testpass')
#         self.assertTrue(login)
#         # request = self.client.get(self.url, data)
#         # self.assertSuccess(request)
#         #
#         # # check if it is the same user
#         # self.assertEqual(request.data['count'], 0)

#         # ===============================================
#         #  Check for admin user of the same organization
#         # ===============================================
#         # d1.organization = self.admin_user.organization
#         # d1.save()
#         # d2.organization = self.admin_user.organization
#         # d2.save()

#         request = self.client.get(self.url, data)
#         print request
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 2)

#         d1.delete()

#         request = self.client.get(self.url, data)
#         self.assertSuccess(request)

#         # check if it is the same instance
#         self.assertEqual(request.data['count'], 1)

#         # logout
#         self.client.logout()


class DesignationDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(DesignationDetailsAPITest, self).setUp()
        # create a designation
        self.designation = DesignationFactory(
            organization=self.admin_user.organization)

        self.url = reverse('designation-details', args=[self.designation.alias])

    def test_designation_details_get(self):
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
        self.assertEqual(request.data['id'], self.designation.pk)

        # logout
        self.client.logout()

    def test_designation_details_put(self):
        data = {
            'name': self.fake.first_name(),
            'department': DepartmentFactory().pk,
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
        self.assertEqual(request.data['department'], data['department'])
        self.assertEqual(request.data['description'], data['description'])

        # logout
        self.client.logout()

    def test_designation_details_delete(self):
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
            phone=self.admin_user.phone, password='testpass')
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


class DesignationDepartmentAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(DesignationDepartmentAPITest, self).setUp()
        # create a designation
        self.department = DepartmentFactory(
            organization=self.admin_user.organization)
        self.designation = DesignationFactory(
            organization=self.admin_user.organization, department=self.department)
        # set the url
        self.url = reverse('designation-by-department-details', args=[self.department.alias])

    def test_department_designation_list_get(self):
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
        # # check if it is the same instance
        # self.assertEqual(request.data['count'], 0)

        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        # self.admin_user.organization = self.user.organization
        # self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)
        # check if it is the same instance
        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()
