from django.urls import reverse
from common.test_case import OmisTestCase
from prescription.tests import PrescriptionFactory
from core.tests import PersonOrganizationFactory


class SymptomSearchAPITest(OmisTestCase):
    url = reverse('prescription-search')

    # def setUp(self):
    #     super(SymptomSearchAPITest, self).setUp()

    def test_symptom_search_get(self):
        patient = PersonOrganizationFactory(
            first_name="test",
            last_name="test",
            organization=self.admin_user.organization
        )
        PrescriptionFactory.create_batch(
            10,
            organization=self.admin_user.organization,
            person_organization_patient=patient
        )

        # search data
        data1 = {
            'keyword': 'search',
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
        self.client.logout()

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

        # check with first keyword
        self.assertEqual(request.data['count'], 0)

        # check with another keyword
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 10)

        # logout
        self.client.logout()
