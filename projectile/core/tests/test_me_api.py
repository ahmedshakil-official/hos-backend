from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase


class MeDetailAPITest(OmisTestCase):
    url = reverse('me-details')

    def test_login_user_details_get(self):
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
        # check if it is the same user
        self.assertEqual(request.data['id'], self.user.pk)

        # ===========================================
        #  Check for admin user
        # ===========================================
        self.user.is_staff = True
        self.user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)
        # check if it is the same user
        self.assertEqual(request.data['id'], self.user.pk)

        # logout
        self.client.logout()
