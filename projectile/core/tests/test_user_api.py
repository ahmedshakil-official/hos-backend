import json
from faker import Faker

from django.urls import reverse

from common.enums import Status
from common.test_case import OmisTestCase
from core.tests import PersonFactory, PersonOrganizationFactory, OrganizationFactory

from ..models import Person, Organization
from ..enums import PersonGroupType


class UserListAPITest(OmisTestCase):
    url = reverse('user-list')
    fake = Faker()

    def setUp(self):
        super(UserListAPITest, self).setUp()

    def test_user_list_get(self):
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
        self.assertEqual(request.data['count'], 1)

        person_will_be_deleted = PersonFactory.create_batch(2)

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        person_will_be_deleted[0].delete()

        request = self.client.get(self.url)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()

    def test_user_list_post(self):
        # ===========================================
        #  Check without login
        # ===========================================
        data = {
            'first_name': self.fake.first_name(),
            'last_name': self.fake.last_name(),
            'email': '{}@example.com'.format(self.fake.ssn())
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
        self.assertEqual(Person.objects.count(), 4)

        # ===========================================
        #  Check using a bad email
        # ===========================================
        data = {
            'email': 'bad_email'
        }
        request = self.client.post(self.url, data)
        self.assertBadRequest(request)


class UserDetailsAPITest(OmisTestCase):
    fake = Faker()

    def setUp(self):
        super(UserDetailsAPITest, self).setUp()
        # set the url
        self.url = reverse('user-details', args=[self.user.alias])

    def test_user_details_get(self):
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
        #  Check with admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user of same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)
        self.assertEqual(request.data['id'], self.user.id)

    def test_user_details_put(self):
        data = {
            'first_name': self.fake.first_name(),
            'last_name': self.fake.last_name(),
            'email': '{}@example.com'.format(self.fake.ssn())
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
        self.assertEqual(request.data['email'], data['email'])
        self.assertEqual(request.data['first_name'], data['first_name'])
        self.assertEqual(request.data['last_name'], data['last_name'])

    def test_user_details_inactive(self):
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


class UserSearchAPITest(OmisTestCase):
    url = reverse('user-search-api')
    fake = Faker()

    def setUp(self):
        super(UserSearchAPITest, self).setUp()

    def test_user_list_get(self):
        # first create some persons
        p1 = PersonFactory(first_name="Abba")
        p2 = PersonFactory(first_name="Abbas")

        # search data
        data = {
            'keyword': 'abb'
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data)
        self.assertPermissionDenied(request)

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
        p1.organization = self.admin_user.organization
        p1.save()
        p2.organization = self.admin_user.organization
        p2.save()

        request = self.client.get(self.url, data)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)

        p1.delete()

        request = self.client.get(self.url, data)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()


class UserAccesOrganizationListAPITest(OmisTestCase):

    def setUp(self):
        super(UserAccesOrganizationListAPITest, self).setUp()
        # self.user = PersonFactory()
        self.url = reverse('person-access-organization-list', args=[self.user.alias])

    def test_user_access_organization_list_get(self):
        initialized_organization = Organization.objects.filter(person=self.user).count()
        organization_1 = OrganizationFactory()
        organization_2 = OrganizationFactory()
        # give access in two organization
        PersonOrganizationFactory(
            person=self.user, organization=organization_1, person_group=PersonGroupType.EMPLOYEE)
        PersonOrganizationFactory(
            person=self.user, organization=organization_2, person_group=PersonGroupType.EMPLOYEE)

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
        self.assertSuccess(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # Compare the data with request data
        organization_count = 2 + initialized_organization
        self.assertEqual(len(request.data), organization_count)
        self.assertEqual(
            request.data[0 + initialized_organization]['name'], organization_1.name)
        self.assertEqual(
            request.data[1 + initialized_organization]['name'], organization_2.name)

        # logout
        self.client.logout()
