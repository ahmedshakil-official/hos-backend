from django.urls import reverse
from faker import Faker

from common.test_case import OmisTestCase
from core.tests import PersonOrganizationPatientFactory
from clinic.tests import ServiceConsumedFactory, ServiceConsumedGroupFactory
from clinic.enums import ServiceConsumedType, PathologyStatus


class PathologySampleCollectedListSearchAPITest(OmisTestCase):
    url = reverse('diagnostic-service-consumed-search')
    fake = Faker()

    # def setUp(self):
    #     super(PathologySampleCollectedListSearchAPITest, self).setUp()

    def test_pathology_sample_collected_list_search_request_get(self):
        person_organization = PersonOrganizationPatientFactory(
            first_name=self.fake.first_name(),
            last_name=self.fake.last_name()
        )
        service_consumed_group = ServiceConsumedGroupFactory()
        ServiceConsumedFactory.create_batch(
            10, organization=self.admin_user.organization,
            person=person_organization.person,
            person_organization_patient=person_organization,
            service_consumed_type=ServiceConsumedType.PATHOLOGY,
            service_consumed_group=service_consumed_group,
            sample_test_date=None,
            report_delivered=False
        )

        # search data
        data1 = {
            'keyword': person_organization.first_name,
            'pathology_status': PathologyStatus.SAMPLE_COLLECTED
        }

        data2 = {
            'keyword': 'tt',
            'pathology_status': PathologyStatus.SAMPLE_COLLECTED
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
        self.assertEqual(request.data['count'], 10)

        # check with another keywod
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 0)
        # logout
        self.client.logout()
