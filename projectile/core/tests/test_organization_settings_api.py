import json
import random
from django.urls import reverse

from common.test_case import OmisTestCase
from pharmacy.tests import StorePointFactory,
from . import DesignationFactory
from ..models import OrganizationSetting


class OrganizationSettingListAPITest(OmisTestCase):
    url = reverse('organization-setting')

    def setUp(self):
        super(OrganizationSettingListAPITest, self).setUp()

    def test_organization_setting_get(self):

        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)


        # ===========================================
        #  Check for admin user of the same organization
        # ===========================================
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # compare request data with created data
        self.assertEqual(request.data['count'], 1)

        # logout
        self.client.logout()


class OrganizationSettingAPITest(OmisTestCase):

    def setUp(self):
        super(OrganizationSettingAPITest, self).setUp()

        self.organization_setting = OrganizationSetting.objects.get(
            organization=self.admin_user.organization
            )
        self.url = reverse('organization-setting-details', args=[self.organization_setting.alias])

    def test_organization_setting_detail_get(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check for admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # compare request data with created data
        self.assertEqual(
            request.data['organization']['name'],
            self.organization_setting.organization.name
            )
        self.assertEqual(request.data['alias'], str(self.organization_setting.alias))

        # logout
        self.client.logout()

    def test_organization_setting_detail_put(self):
        data = {
            'organization': self.admin_user.organization.id,
            'default_storepoint': StorePointFactory().id,
        }
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.put(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.put(self.url, data)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.put(
            self.url,
            data=json.dumps(dict(data)),
            content_type='application/json'
        )
        self.assertSuccess(request)

        self.assertEqual(
            request.data['default_storepoint'],
            data['default_storepoint']
        )

        # logout
        self.client.logout()

    def test_organization_setting_detail_delete(self):
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.delete(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with login
        # ===========================================
        login = self.client.login(phone=self.user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.delete(self.url)
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check with admin user
        # ===========================================
        login = self.client.login(
            phone=self.admin_user.phone, password='testpass')
        self.assertTrue(login)
        request = self.client.delete(self.url)
        self.assertDeleted(request)

        # logout
        self.client.logout()
