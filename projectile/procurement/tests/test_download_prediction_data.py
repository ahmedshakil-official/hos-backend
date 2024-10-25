from common.test_case import OmisTestCase
from procurement.tests import url_helpers


class DownloadPredictionDataAPITest(OmisTestCase):

    def test_download_prediction_data(self):

        # get the url from helper function
        url = url_helpers.get_download_prediction_data_url(
            name="create-prediction-data",
        )

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check normal user can't access the endpoint
        # ===========================================
        login = self.client.login(phone=self.user.phone, password="testpass")
        self.assertTrue(login)

        request = self.client.get(url)
        self.assertPermissionDenied(request)

        # user logout
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password="testpass")
        self.assertTrue(login)
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        # Check that get method is not allowed.
        request = self.client.get(url)
        self.assertSuccess(request)

        # logout admin user
        self.client.logout()
