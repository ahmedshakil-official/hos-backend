from common.test_case import OmisTestCase


from . import url_helpers

from procurement.tests import PurchasePredictionFactory


class PurchasePredictionIsLockedUpdateAPITest(OmisTestCase):

    def test_purchase_prediction_is_locked_update(self):
        # Create a purchase prediction by calling factory
        purchase_prediction = PurchasePredictionFactory.create(is_locked=False)
        prediction_file = purchase_prediction.prediction_file
        # get the url from helper function
        url = url_helpers.get_purchase_prediction_is_locked_update_url(
            name="purchase-prediction-is-locked-update",
            alias=prediction_file.alias
        )
        payload = {
            "is_locked": True
        }

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.patch(url, payload)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check normal user can't access the endpoint
        # ===========================================
        login = self.client.login(phone=self.user.phone, password="testpass")
        self.assertTrue(login)

        request = self.client.patch(url, payload)
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
        self.assertMethodNotAllowed(request)

        # Update by patch method
        request = self.client.patch(url, payload)
        self.assertSuccess(request)
        # Check that is_locked is updated to true in the respone
        respone = request.json()
        self.assertEqual(respone["is_locked"], True)
        # Check is it updated on DB or not
        purchase_prediction.refresh_from_db()
        self.assertEqual(purchase_prediction.is_locked, True)

        # logout admin user
        self.client.logout()

        # ===========================================
        #  Check for Procurement Manager
        # ===========================================
        login = self.client.login(phone=self.user.phone, password="testpass")
        self.assertTrue(login)
        self.provide_permission_to_user(
            permission_group=self.procurement_manager_group,
            user=self.user
        )

        # Update by patch method
        request = self.client.patch(url, payload)
        self.assertSuccess(request)

        #logout user
        self.client.logout()

        # ===========================================
        #  Check for Distribution T1
        # ===========================================
        login = self.client.login(phone=self.user.phone, password="testpass")
        self.assertTrue(login)
        self.provide_permission_to_user(
            permission_group=self.distribution_t1_group,
            user=self.user
        )

        # Update by patch method
        request = self.client.patch(url, payload)
        self.assertSuccess(request)

        # logout client
        self.client.logout()
