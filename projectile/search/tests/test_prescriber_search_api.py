from django.urls import reverse
from common.test_case import OmisTestCase
from core.tests import (
    PersonOrganizationEmployeeFactory,
    DesignationFactory,
    PrescriberDesignationFactory
)
from core.models import OrganizationSetting
from core.enums import PersonGroupType
from common.enums import Status


class PrescriberSearchAPITest(OmisTestCase):
    url = reverse('prescriber-search')

    # def setUp(self):
    #     super(PrescriberSearchAPITest, self).setUp()

    def test_prescriber_list_search_get(self):
        employee_designation = DesignationFactory(
            organization=self.admin_user.organization,
            status=Status.ACTIVE
        )
        organization_setting = OrganizationSetting.objects.get(
            organization=self.admin_user.organization.id
        )
        prescriber_designantion = PrescriberDesignationFactory(
            employee_designation=employee_designation,
            organization_settings=organization_setting
        )
        person = PersonOrganizationEmployeeFactory.create_batch(
            2, first_name="test", last_name="test",
            organization=self.admin_user.organization,
            designation=employee_designation,
            person_group=PersonGroupType.PRESCRIBER
        )

        # search data
        data1 = {
            'keyword': 'les',
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
        self.assertSuccess(request)

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

        self.assertEqual(request.data['count'], 2)
        self.assertEqual(
            request.data['results'][0]['first_name'],
            person[1].first_name)
        self.assertEqual(
            request.data['results'][0]['last_name'],
            person[1].last_name)

        self.assertEqual(
            request.data['results'][1]['first_name'],
            person[0].first_name)
        self.assertEqual(
            request.data['results'][1]['last_name'],
            person[0].last_name)

        # Delete one prescriber instance
        person[0].delete()
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 1)
        # logout
        self.client.logout()
