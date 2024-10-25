from django.urls import reverse

from common.test_case import OmisTestCase

from ..tests import UnitFactory


class UnitMergeAPITest(OmisTestCase):
    url = reverse("unit-merge")

    def tes_unit_merge(self):

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ==========================================
        # Normal user login
        # ==========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        # admin and superadmin  login
        # ===========================================

        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # ===========================================
        # Post method access
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertEqual(request.status_code, 405,
                         text="All method should be restricted except Post")

        # ===========================================
        # merge unit
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        first_unit = UnitFactory()
        seconed_unit = UnitFactory()
        data = {
            'unit': first_unit.id,
            'clone_unit': seconed_unit.id
        }
        request = self.client.post(self.url, data)
        self.assertSuccess(request)
