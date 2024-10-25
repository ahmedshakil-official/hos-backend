from django.utils import timezone

from common.test_case import OmisTestCase

from procurement.enums import ProcureDateUpdateType
from procurement.tests import url_helpers

from . import payloads, ProcureFactory, ProcureGroupFactory


class ProcureDateUpdateAPITest(OmisTestCase):
    url = url_helpers.get_procure_date_update_url()

    def test_procure_date_update_post(self):
        # Clear permission cache
        self.clear_permission_cache(
            user=self.user, permission_group=self.procurement_coordinator_group
        )

        #  Check without login
        request = self.client.get(path=self.url)
        self.assertPermissionDenied(request)

        #  Check normal user can't access the endpoint
        login = self.client.login(phone=self.user.phone, password="testpass")
        self.assertTrue(login)

        # Giving permission to the user as an admin
        login = self.client.login(phone=self.admin_user.phone, password="testpass")
        self.assertTrue(login)

        # Procure group factory creation
        procure_group = ProcureGroupFactory()

        # Updating data using POST request
        procure = ProcureFactory()
        procure_for_group = ProcureFactory()
        procure_date = procure.date
        payload = payloads.procure_date_update_payload(
            procure.alias, True, ProcureDateUpdateType.ADVANCE
        )
        request = self.client.post(self.url, payload)
        self.assertSuccess(request)
        updated_date = procure.date
        self.assertEqual(procure_date, updated_date)

        # Check if the created date and procure date are the same when advancing procure date
        procure_mismatch_date = ProcureFactory(
            date=timezone.now() + timezone.timedelta(days=1)
        )
        procure_date = procure_mismatch_date.date
        payload = payloads.procure_date_update_payload(
            procure_mismatch_date.alias, True, ProcureDateUpdateType.ADVANCE
        )
        request = self.client.post(self.url, payload)
        self.assertBadRequest(request)

        # Check if the created date and procure date are not same when reversing advance procure date
        procure_for_reversing_advance = ProcureFactory()
        payload = payloads.procure_date_update_payload(
            procure_for_reversing_advance.alias,
            True,
            ProcureDateUpdateType.REVERSE_ADVANCE,
        )
        request = self.client.post(self.url, payload)
        self.assertBadRequest(request)

        # Checking If the procure is part of a group, update all procures in the group
        procure_for_group = ProcureFactory()
        procure_for_group.procure_group = procure_group
        procure_for_group.save()
        procure_for_group_date = procure_for_group.date
        payload = payloads.procure_date_update_payload(
            procure_for_group.alias, True, ProcureDateUpdateType.ADVANCE
        )
        request = self.client.post(self.url, payload)
        self.assertSuccess(request)
        procure_group_updated_date = procure_for_group.date
        self.assertEqual(procure_for_group_date, procure_group_updated_date)

        # If the procure is not part of a group, update its date
        procure_with_no_group = ProcureFactory()
        procure_with_no_group_date = procure_with_no_group.date
        payload = payloads.procure_date_update_payload(
            procure_with_no_group.alias, True, ProcureDateUpdateType.ADVANCE
        )
        request = self.client.post(self.url, payload)
        self.assertSuccess(request)
        procure_with_no_group_updated_date = procure_with_no_group.date
        self.assertEqual(procure_with_no_group_date, procure_with_no_group_updated_date)

        # If confirmation is not requested and procure is part of a group, provide an error response
        procure_without_confirmation = ProcureFactory()
        procure_without_confirmation.procure_group = procure_group
        procure_without_confirmation.save()
        payload = payloads.procure_date_update_payload(
            procure_without_confirmation.alias, False, ProcureDateUpdateType.ADVANCE
        )
        request = self.client.post(self.url, payload)
        self.assertBadRequest(request)

        # If confirmation is not requested and procure is not part of a group, update its date
        procure_without_confirmation = ProcureFactory()
        payload = payloads.procure_date_update_payload(
            procure_without_confirmation.alias, False, ProcureDateUpdateType.ADVANCE
        )
        request = self.client.post(self.url, payload)
        self.assertSuccess(request)

        # Clear permission cache
        self.clear_permission_cache(
            user=self.user, permission_group=self.procurement_coordinator_group
        )

        # logout user
        self.client.logout()

        #  Checking for allowed and unallowed permissions
        available_permissions = [
            self.admin_group,
            self.distribution_t1_group,
            self.procurement_group,
            self.procurement_manager_group,
            self.procurement_coordinator_group,
            # TODO: need to check permission [StaffIsProcurementBuyerWithSupplier]
        ]
        unallowed_permissions = [self.distribution_t2_group]
        self.check_with_different_permissions(
            available_permissions=available_permissions,
            user=self.user,
            url=self.url,
            unallowed_permissions=unallowed_permissions,
        )
