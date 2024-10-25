from common.test_case import OmisTestCase

from ..models import Procure
from . import url_helpers

from procurement.tests import ProcureFactory


class ProcureShopNamesAPITest(OmisTestCase):
    url = url_helpers.get_shop_names_url("procure-shop-name-list")

    def test_procure_shop_names_list(self):
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

        # user logout
        self.client.logout()

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password="testpass")
        self.assertTrue(login)
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # Create 2 procures instance by calling procure factory.
        procures = ProcureFactory.create_batch(2)

        # ===========================================
        #  Check response data
        # ===========================================
        response = self.client.get(self.url)
        response_data = response.data
        # check that response object has 2 shop_names
        self.assertEqual(len(response_data), 2)

        # logout admin user
        self.client.logout()

        # ===========================================
        #  Check for allowed and unallowed permissions
        # ===========================================
        available_permissions = [
            self.procurement_group,
            self.procurement_manager_group,
            self.distribution_t1_group,
        ]
        unallowed_permissions = [self.distribution_t2_group]
        self.check_with_different_permissions(
            available_permissions=available_permissions,
            user=self.user,
            url=self.url,
            unallowed_permissions=unallowed_permissions,
        )
