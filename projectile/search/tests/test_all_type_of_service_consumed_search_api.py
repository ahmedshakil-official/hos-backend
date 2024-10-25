import uuid
from faker import Faker
from django.urls import reverse
from common.test_case import OmisTestCase
from core.tests import PersonOrganizationFactory
from clinic.tests import ServiceConsumedFactory
from clinic.enums import ServiceConsumedType


class AllTypeOFServiceConsumedSearchListAPITest(OmisTestCase):
    url = reverse('all-type-service-consumed-search')
    fake = Faker()

    # def setUp(self):
    #     super(AllTypeOFServiceConsumedSearchListAPITest, self).setUp()

    def test_all_type_of_service_consumed_search_get(self):
        person_organization1 = PersonOrganizationFactory(
            first_name=self.fake.first_name() + str(uuid.uuid4()),
            organization=self.admin_user.organization
        )
        person_organization2 = PersonOrganizationFactory(
            first_name=self.fake.first_name(),
            organization=self.admin_user.organization
        )
        ServiceConsumedFactory(
            organization=self.admin_user.organization,
            person_organization_patient=person_organization1,
            service_consumed_type=ServiceConsumedType.PATHOLOGY
        )
        ServiceConsumedFactory(
            organization=self.admin_user.organization,
            person_organization_patient=person_organization2,
            service_consumed_type=ServiceConsumedType.DEFAULT
        )

        # search data
        data1 = {
            'keyword': 'search',
        }

        data2 = {
            'keyword': person_organization1.first_name,
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login but not as admin
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        self.client.logout()

        # ===========================================
        #  Check with login but as admin and owner
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 0)

        # check with another keyword
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()