from rest_framework import status

from common.test_case import OmisTestCase

from . import url_helpers, ProcureFactory, ProcureStatusFactory

from .payloads import procure_status_payload

from .utils import check_procure_status_list_fields


class ProcureStatusListCreateTest(OmisTestCase):
    url = url_helpers.get_procure_status_url("procure-status-list-create")

    def test_procure_status_create(self):
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
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password="testpass")
        self.assertTrue(login)
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # ===========================================
        #  Create Procure Status
        # ===========================================
        # Create a Procure instance
        procure = ProcureFactory.create()

        payload = procure_status_payload(procure.id)

        # Make a POST request to create a Procure Status using the prepared payload
        response = self.client.post(self.url, payload)

        # Assert that the status code is HTTP 201 Created
        self.assertTrue(response.status_code, status.HTTP_201_CREATED)

        response_data = response.data

        # Check if the response data contains the expected fields and values
        self.assertIn("id", response_data)
        self.assertIn("id", response_data)
        self.assertEqual(payload["current_status"], response_data["current_status"])
        self.assertEqual(payload["procure"], response_data["procure"])
        self.assertEqual(payload["remarks"], response_data["remarks"])

        # logout admin user
        self.client.logout()

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

    def test_procure_status_list(self):
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
        #  Check for admin user
        # ===========================================
        login = self.client.login(phone=self.admin_user.phone, password="testpass")
        self.assertTrue(login)
        self.admin_user.organization = self.user.organization
        self.admin_user.save()
        request = self.client.get(self.url)
        self.assertSuccess(request)

        # Create 2 procure status by calling procure status factory.
        ProcureStatusFactory.create_batch(2)

        # ===========================================
        #  Check response data
        # ===========================================
        response = self.client.get(self.url)
        response_data = response.data

        # check that response object has 2 procure statuses
        self.assertEqual(len(response_data["results"]), 2)

        # Check if each result in response_data has the expected fields
        check_procure_status_list_fields(self, response)

        # logout admin user
        self.client.logout()

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
