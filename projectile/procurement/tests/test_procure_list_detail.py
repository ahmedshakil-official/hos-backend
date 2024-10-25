import pprint

from common.test_case import OmisTestCase

from core.models import PersonOrganizationGroupPermission

from ..models import Procure
from . import url_helpers, ProcureFactory
from . utils import (
    update_procure_organization_with_user_organization,
    check_procure_list_fields
)


class ProcureListCreateAPITest(OmisTestCase):

    url = url_helpers.get_procure_url("procure-list-create")

    def test_procure_list_for_coordinator(self):
        from core.models import PersonOrganization

        self.clear_permission_cache(
            user=self.user,
            permission_group=self.procurement_coordinator_group
        )
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

        # add permission by orm
        self.provide_permission_to_user(permission_group=self.procurement_coordinator_group)

        # check HealthOS use can access the link
        login = self.client.login(phone=self.user.phone, password="testpass")
        self.assertTrue(login)

        procure = ProcureFactory()
        update_procure_organization_with_user_organization(
            procure=procure,
            organization_id=self.user.organization.id
        )

        # create a procure with different organization the user
        ProcureFactory()

        # make sure we have two procure instance
        db_procure_count = Procure().get_all_actives().count()
        self.assertEqual(db_procure_count, 2)

        # make request and check response status
        request = self.client.get(self.url)
        self.assertSuccess(request=request)

        # check if user only getting one procure
        self.assertEqual(request.json()["count"], 1)
        self.assertNotEqual(request.json()["count"], 2)

        # check if any field missing in response from previously defined in serializer
        check_procure_list_fields(self, request=request)

        # user logout and clear permission cache
        self.clear_permission_cache(
            user=self.user,
            permission_group=self.procurement_coordinator_group
        )
        self.client.logout()
