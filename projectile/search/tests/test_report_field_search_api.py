from faker import Faker
from django.urls import reverse
from common.test_case import OmisTestCase
from clinic.tests import SubServiceReportFieldFactory, SubServiceFactory, ServiceFactory
from clinic.enums import ServiceType


class ReportFieldSearchAPITest(OmisTestCase):
    url = reverse('report-field-search')
    fake = Faker()

    # def setUp(self):
    #     super(ReportFieldSearchAPITest, self).setUp()

    def test_report_field_search_get(self):
        service = ServiceFactory(type=ServiceType.DIAGNOSTIC)
        sub_service = SubServiceFactory(service=service)
        report_field_name = self.fake.first_name()
        report_field = SubServiceReportFieldFactory.create_batch(
            2,
            name=report_field_name,
            organization=self.admin_user.organization,
            sub_service=sub_service
        )

        # search data
        data1 = {
            'keyword': 'les',
        }

        data2 = {
            'keyword': report_field_name,
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
        self.assertEqual(request.data['count'], 2)

        # sort data by id
        request.data['results'] = sorted(
            request.data['results'], key=lambda id: id['id']
        )

        self.assertEqual(
            request.data['results'][0]['name'],
            report_field[0].name)
        self.assertEqual(
            request.data['results'][0]['alias'],
            str(report_field[0].alias))

        self.assertEqual(
            request.data['results'][1]['name'],
            report_field[1].name)
        self.assertEqual(
            request.data['results'][1]['alias'],
            str(report_field[1].alias))

        # delete first entry
        report_field[0].delete()

        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        # check if it is the same user
        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()
