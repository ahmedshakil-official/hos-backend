from django.urls import reverse

from common.test_case import OmisTestCase
from core.tests import PatientFactory, PersonOrganizationFactory
from core.models import PersonOrganization
from account.tests import PatientBillFactory


class PatientBillSearchAPITest(OmisTestCase):
    url = reverse('patient-bill-search')

    # def setUp(self):
    #     super(PatientBillSearchAPITest, self).setUp()

    def test_patient_bill_search_list(self):
        # first create some patient bill
        person = PatientFactory.create_batch(
            2, first_name='test', organization=self.admin_user.organization)
        person_organization = PersonOrganization.objects.get(
            person=person[0].id, organization=self.admin_user.organization.id)
        another_person_organization = PersonOrganization.objects.get(
            person=person[1].id, organization=self.admin_user.organization.id)
        data1 = PatientBillFactory(person_organization_patient=person_organization)
        data2 = PatientBillFactory(person_organization_patient=another_person_organization)

        # search data
        search_data = {
            'keyword': 'te'
        }
        search_data2 = {
            'keyword': 'zzz'
        }
        search_data3 = {
            'keyword': data1.id
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url, search_data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, search_data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url, search_data)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 0)

        # ===============================================
        #  Check for admin user of the same organization
        # ===============================================
        data1.organization = self.admin_user.organization
        data1.save()
        data2.organization = self.admin_user.organization
        data2.save()

        # check with random data
        request = self.client.get(self.url, search_data2)
        self.assertSuccess(request)

        # check if it is the same instance
        self.assertEqual(request.data['count'], 0)

        # check with integer keyword as id
        request = self.client.get(self.url, search_data3)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 1)

        # check if it is the same instance with keyword 'test'
        request = self.client.get(self.url, search_data)
        self.assertSuccess(request)
        self.assertEqual(request.data['count'], 2)

        # delete an instance
        data1.delete()

        # check if it is the same instance with keyword 'test'
        request = self.client.get(self.url, search_data)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()
