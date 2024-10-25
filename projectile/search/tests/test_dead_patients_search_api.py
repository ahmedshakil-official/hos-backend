from faker import Faker
from django.urls import reverse
from common.test_case import OmisTestCase
from common.enums import Status
from core.tests import PatientFactory
from core.models import PersonOrganization
from core.enums import PersonDropoutStatus


class PatientDeadListSearchAPITest(OmisTestCase):
    url = reverse('dead-patient-list-search')
    fake = Faker()

    # def setUp(self):
    #     super(PatientDeadListSearchAPITest, self).setUp()

    def test_organization_person_list_get(self):
        patient = PatientFactory(
            organization=self.admin_user.organization,
            status=Status.ACTIVE,
            first_name='Test',
            last_name='Test'
        )
        person_organization = PersonOrganization.objects.get(
            status=Status.ACTIVE,
            organization=self.admin_user.organization,
            person=patient.id
        )
        person_organization.dropout_status = PersonDropoutStatus.DEAD
        person_organization.save()
        # search data
        data1 = {
            'keyword': 'Tt',
        }

        data2 = {
            'keyword': 'test',
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        request = self.client.get(self.url, data1)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 0)

        # check with another keywod
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 1)
        self.assertEqual(
            request.data['results'][0]['first_name'],
            patient.first_name)
        self.assertEqual(
            request.data['results'][0]['last_name'],
            patient.last_name)

        # logout
        self.client.logout()
