from common.test_case import OmisTestCase

from .payloads import get_procure_issue_log_payload
from . import url_helpers
from .utils import check_procure_issue_log_list_fields

from pharmacy.tests import StockFactory
from core.tests import (
    PersonOrganizationSupplierFactory,
    PersonOrganizationEmployeeFactory,
)
from procurement.tests import (
    ProcureIssueLogFactory,
    PredictionItemFactory,
)


class ProcureIssueLogAPITest(OmisTestCase):
    url = url_helpers.get_shop_names_url("procure-issue-list-create")

    def test_procure_issue_log_list(self):
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

        # Create 2 procure issue log instance by calling procure issue log factory.
        procures_issue_log = ProcureIssueLogFactory.create_batch(
            size=2, organization_id=self.admin_user.organization_id
        )

        # ===========================================
        #  Check response data
        # ===========================================
        request = self.client.get(self.url)
        self.assertSuccess(request=request)
        # Check that response has 2 procure issue log data
        self.assertEqual(request.json()["count"], 2)

        # check if any field missing in response from previously defined in serializer
        check_procure_issue_log_list_fields(self, request=request)
        # logout admin user
        self.client.logout()

        # ===========================================
        #  Check for allowed and unallowed permissions
        # ===========================================
        available_permissions = [
            self.procurement_group,
            self.procurement_manager_group,
            self.procurement_coordinator_group,
            self.distribution_t1_group,
        ]
        unallowed_permissions = [self.distribution_t2_group]
        self.check_with_different_permissions(
            available_permissions=available_permissions,
            user=self.user,
            url=self.url,
            unallowed_permissions=unallowed_permissions,
        )

    def test_procure_issue_log_post(self):
        # Prepare stock supplier employee to create payload
        organization_id = self.admin_user.organization_id
        supplier = PersonOrganizationSupplierFactory.create(
            organization_id=organization_id
        )
        stock = StockFactory.create(organization_id=organization_id)
        prediction_item = PredictionItemFactory.create(organization_id=organization_id)
        payload = get_procure_issue_log_payload(
            supplier_id=supplier.id,
            employee_id=self.person_organization_employee.id,
            stock_id=stock.id,
            prediction_item_id=prediction_item.id,
        )
        # ===========================================
        #  Check without login
        # ===========================================
        request = self.client.post(self.url, payload, format="json")
        self.assertPermissionDenied(request)

        # ===========================================
        #  Check normal user can't post to the endpoint
        # ===========================================
        login = self.client.login(phone=self.user.phone, password="testpass")
        self.assertTrue(login)

        request = self.client.post(self.url, payload, format="json")
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
        request = self.client.post(self.url, payload, format="json")

        # self.assertCreated(request=request)
        response_json = request.json()

        # check the created field are same as provided
        self.assertIn("id", response_json)
        self.assertIn("alias", response_json)
        self.assertIn("date", response_json)
        self.assertEqual(payload["employee"], response_json["employee"])
        self.assertEqual(payload["supplier"], response_json["supplier"])
        self.assertEqual(payload["prediction_item"], response_json["prediction_item"])
        self.assertEqual(payload["type"], response_json["type"])
        self.assertEqual(payload["remarks"], response_json["remarks"])
        self.assertEqual("{}", response_json["geo_location_data"])

        # logout user
        self.client.logout()
