from django.urls import reverse
from faker import Faker
import uuid

from common.test_case import OmisTestCase
from core.tests import PersonOrganizationPatientFactory
from clinic.tests import ServiceConsumedFactory, ServiceConsumedGroupFactory
from clinic.enums import ServiceConsumedType, PathologyStatus


class ServiceConsumedSearchAPITest(OmisTestCase):
    url = reverse('service-consumed-search')
    fake = Faker()

    # def setUp(self):
    #     super(ServiceConsumedSearchAPITest, self).setUp()

    def test_service_consumed_search_request_get(self):
        person_organization = PersonOrganizationPatientFactory(
            first_name=self.fake.first_name() + str(uuid.uuid4()),
            last_name=self.fake.last_name()
        )
        service_consumed = ServiceConsumedFactory.create_batch(
            2, organization=self.admin_user.organization,
            person=person_organization.person,
            person_organization_patient=person_organization,
            service_consumed_type=ServiceConsumedType.DEFAULT,
            sample_test_date=None
        )

        # search data
        data1 = {
            'keyword': person_organization.first_name
        }

        data2 = {
            'keyword': 'tt'
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
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 2)
        # check with another keywod
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 0)

        # Delete the first instance
        service_consumed[0].delete()
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()
