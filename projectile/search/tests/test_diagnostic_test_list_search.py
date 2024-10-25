from django.urls import reverse

from common.test_case import OmisTestCase

from clinic.tests import (
    SubServiceFactory,
    InvestigationFieldFactory,
    ReportFieldCategoryFactory,
    ServiceFactory,
    DiagnosticTestSampleFactory,
    SubServiceReportFieldFactory,
)
from prescription.tests import LabTestFactory


class DiagnosticTestListSearchAPITest(OmisTestCase):
    url = reverse('diagnostic-test-search')

    # def setUp(self):
    #     super(DiagnosticTestListSearchAPITest, self).setUp()

    def test_diagnostic_test_list_search(self):
        # create labtest
        labtest = LabTestFactory.create_batch(
            2, name="test", organization=self.admin_user.organization)

        # create two subservice
        subservice = SubServiceFactory(
            organization=self.admin_user.organization,
            labtest=labtest[0],
        )
        subservice2 = SubServiceFactory(
            organization=self.admin_user.organization,
            labtest=labtest[1],
        )

        # create two subservice report field for investigation field with those two sub service
        created_data = SubServiceReportFieldFactory.create_batch(
            2,
            sub_service=subservice,
            organization=self.admin_user.organization
        )
        created_data2 = SubServiceReportFieldFactory.create_batch(
            4,
            sub_service=subservice2,
            organization=self.admin_user.organization,
        )

        # search data
        data1 = {
            'keyword': 'tes',
        }

        data2 = {
            'keyword': 'zzz',
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
        self.assertEqual(request.data['count'], 2)

        # check with another keywod
        request = self.client.get(self.url, data2)
        self.assertSuccess(request)

        self.assertEqual(request.data['count'], 0)
        # logout
        self.client.logout()
