from common.test_case import OmisTestCase
from procurement.tests import url_helpers


class InvoiceNumberForProcureAPITest(OmisTestCase):
    url = url_helpers.get_procure_status_url("get-invoice-number-for-creating-procure")

    def test_get_invoice_number_for_procure(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(path=self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check normal user can't access the endpoint
        # ===========================================
        login = self.client.login(phone=self.user.phone, password="testpass")
        self.assertTrue(login)

        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check after giving permission to user
        # ===========================================

        # add permission by orm
        self.provide_permission_to_user(permission_group=self.procurement_coordinator_group)
        response = self.client.get(self.url)
        self.assertSuccess(response)

        # check that invoice_number is available in the response
        self.assertIn("invoice_number", response.json())

        # ===========================================
        #  Check for allowed and unallowed permissions
        # ===========================================
        available_permissions = [
            self.admin_group,
            self.distribution_t1_group,
            self.procurement_group,
            self.procurement_manager_group,
            self.procurement_coordinator_group,
        ]
        unallowed_permissions = [self.distribution_t2_group]
        self.check_with_different_permissions(
            available_permissions=available_permissions,
            user=self.user,
            url=self.url,
            unallowed_permissions=unallowed_permissions,
        )

        # logout user
        self.client.logout()