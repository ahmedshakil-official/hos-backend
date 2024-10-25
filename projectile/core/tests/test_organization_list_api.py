from django.urls import reverse
from faker import Faker
from common.test_case import OmisTestCase
from core.tests import OrganizationFactory


class OrganizationListAPITest(OmisTestCase):
    url = reverse('organization-list')
    fake = Faker()

    def setUp(self):
        super(OrganizationListAPITest, self).setUp()

    def test_organization_list_get(self):
        organization = OrganizationFactory.create_batch(
            2
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
        self.client.logout()
        # ===========================================
        #  Check for admin user
        # ===========================================
        self.admin_user.is_superuser = True
        self.admin_user.save()
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        del request.data['results'][2]
        del request.data['results'][2]

        self.assertSuccess(request)



        # check if it is the same user
        self.assertEqual(request.data['results'][0]['id'], organization[1].id)
        # self.assertEqual(request.data['results'][0]['slogan'], str(organization[1].slogan))
        self.assertEqual(request.data['results'][0]['name'], organization[1].name)
        self.assertEqual(request.data['results'][0]['contact_person'],
                         organization[1].contact_person)
        self.assertEqual(request.data['results'][0]['contact_person_designation'],
                         organization[1].contact_person_designation)

        self.assertEqual(request.data['results'][1]['id'], organization[0].id)
        # self.assertEqual(request.data['results'][1]['slogan'], str(organization[0].slogan))
        self.assertEqual(request.data['results'][1]['name'], organization[0].name)
        self.assertEqual(request.data['results'][1]['contact_person'],
                         organization[0].contact_person)
        self.assertEqual(request.data['results'][1]['contact_person_designation'],
                         organization[0].contact_person_designation)
        # logout
        self.client.logout()

    def test_organization_list_post(self):
        # ===========================================
        #  Create data for post
        # ===========================================
        data = {
            'name': self.fake.first_name(),
            'address': self.fake.last_name(),
            'primary_mobile': self.fake.msisdn(),
            'contact_person': self.fake.last_name(),
            'contact_person_designation': self.fake.first_name(),
            # 'slogan': self.fake.ssn(),
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
        self.admin_user.is_superuser = True
        self.admin_user.save()
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.post(self.url, data)
        self.assertCreated(request)
        # check if it is the same user
        self.assertEqual(request.data['name'], data['name'])
        # self.assertEqual(request.data['slogan'], data['slogan'])
        self.assertEqual(request.data['address'], data['address'])
        self.assertEqual(request.data['contact_person'], data['contact_person'])
        self.assertEqual(request.data['contact_person_designation'],
                         data['contact_person_designation'])
        self.assertEqual(request.data['primary_mobile'], data['primary_mobile'])
        # logout
        self.client.logout()
