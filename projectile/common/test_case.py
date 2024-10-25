from io import BytesIO
from PIL import Image

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from core.enums import PersonGroupType
from core.tests import (
    PersonFactory,
    GroupPermissionFactory,
    PersonOrganizationFactory,
    PersonOrganizationGroupPermissionFactory,
)
# from search.indexes import get_index


# pylint: disable=invalid-name
class OmisTestCase(TestCase):

    def setUp(self):
        # Client
        self.client = APIClient()

        # Users
        self.user = PersonFactory(person_group=PersonGroupType.EMPLOYEE)
        self.admin_user = PersonFactory(
            is_staff=True,
            is_superuser=True,
            person_group=PersonGroupType.SYSTEM_ADMIN
        )
        self.employee_user = PersonFactory(
            is_staff=True,
            person_group=PersonGroupType.EMPLOYEE
        )

        # Group
        self.admin_group = GroupPermissionFactory(name='Admin')
        self.accounts_group = GroupPermissionFactory(name="Accounts")
        self.nurse_group = GroupPermissionFactory(name="Nurse")
        self.salesman_group = GroupPermissionFactory(name="Salesman")
        self.procurement_group = GroupPermissionFactory(name="Procurement")
        self.prescriber_group = GroupPermissionFactory(name="Prescriber")
        self.sales_return_group = GroupPermissionFactory(name="SalesReturn")
        self.adjustment_group = GroupPermissionFactory(name="Adjustment")
        self.delivery_man_group = GroupPermissionFactory(name="DeliveryMan")
        self.procurement_over_purchase_group = GroupPermissionFactory(name="ProcurementOverPurchase")
        self.prediction_item_worse_rate_edit_group = GroupPermissionFactory(name="PredictionItemWorstRateEdit")
        self.tele_marketing_group = GroupPermissionFactory(name="TeleMarketing")
        self.older_invoice_status_change_group = GroupPermissionFactory(name="OlderInvoiceStatusChange")
        self.marketing_group = GroupPermissionFactory(name="Marketing")
        self.delivery_hub_group = GroupPermissionFactory(name="DeliveryHub")
        self.distribution_t1_group = GroupPermissionFactory(name="Distribution T1")
        self.distribution_t2_group = GroupPermissionFactory(name="Distribution T2")
        self.distribution_t3_group = GroupPermissionFactory(name="Distribution T3")
        self.front_desk_product_return_group = GroupPermissionFactory(name="Front Desk (Product Return)")
        self.procurement_manager_group = GroupPermissionFactory(name="Procurement Manager")
        self.sales_coordinator_group = GroupPermissionFactory(name="Sales Coordinator")
        self.sales_manager_group = GroupPermissionFactory(name="Sales Manager")
        self.procurement_coordinator_group = GroupPermissionFactory(name="Procurement Coordinator")

        # Person Organization
        self.person_organization = PersonOrganizationFactory(
            person=self.admin_user,
            organization=self.admin_user.organization,
            person_group=PersonGroupType.OTHER
        )
        self.person_organization_employee = self.employee_user.get_person_organization_for_employee()

        # Person Organization Group Permission
        PersonOrganizationGroupPermissionFactory(
            person_organization=self.person_organization,
            permission=self.admin_group
        )
        self.employee_group_permission = PersonOrganizationGroupPermissionFactory(
            person_organization=self.person_organization_employee,
            permission=self.accounts_group
        )

        # Others
        self.countGroupPermission = 23

    def clear_permission_from_db(self, user=None):
        """Clear existing permission from db for the user."""
        # Import necessary module
        from core.models import PersonOrganizationGroupPermission
        # Set the user according to the argument or default to self.user
        user = user if user else self.user

        PersonOrganizationGroupPermission.objects.filter(
            person_organization_id=self.user.person_organization.first().id,
        ).delete()

    def clear_permission_cache(self, permission_group, user=None):
        """
        Clears the permission cache for a specific permission group and user.

        Args:
        - permission_group (str): The name of the permission group.
        - user (User, optional): The user for whom the cache needs to be cleared.
                                 If not provided, the default user of the instance is used.

        Returns:
        - None

        Note:
        - This function clears the cache for a specific permission group and user,
          using the Django cache framework.

        """

        # Import necessary modules
        from common.utils import get_permission_cache_key
        from django.core.cache import cache

        # Set the user according to the argument or default to self.user
        user = user if user else self.user

        # delete permissions from db by calling the clear permission method
        self.clear_permission_from_db(user=user)

        # Clear cache before assigning new permission
        cache_key = get_permission_cache_key(
            person_id=user.id,
            organization_id=user.organization_id,
            group_name=permission_group
        )
        cache.delete(key=cache_key)


    def provide_permission_to_user(self, permission_group, user=None):
        """
        Provides a specific permission group to a user and clears the permission cache.

        Args:
        - permission_group: The permission group to be provided.
        - user (User, optional): The user to whom the permission is to be granted.
                                 If not provided, the default user of the instance is used.

        Returns:
        - None

        Note:
        - This function grants a specified permission group to a user by creating a record
          in the PersonOrganizationGroupPermission model and clears the permission cache.
        """

        # Import necessary module
        from core.models import PersonOrganizationGroupPermission

        # Set the user according to the argument or default to self.user
        user = user if user else self.user

        # Clear permission cache for the user and permission group
        self.clear_permission_cache(
            user=user,
            permission_group=permission_group
        )

        # Add permission to the user with the given permission group
        PersonOrganizationGroupPermission.objects.create(
            person_organization_id=self.user.person_organization.first().id,
            permission_id=permission_group.id
        )
    def perform_request_with_permission(
        self, permission_group, user, url, has_permission: bool = True
    ):
        """
        Perform a request with a specific permission for a user and assert the result based on permission status.

        Args:
        - permission_group (str): The permission group to be assigned.
        - user (User): The user for whom the permission is being assigned.
        - url (str): The URL to perform the request.
        - has_permission (bool, optional): Flag indicating whether the user should have permission (default: True).

        Returns:
        - None

        Raises:
        - AssertionError: If permission is not granted or denied as expected.
        """
        # Login with the client
        login = self.client.login(phone=self.user.phone, password="testpass")
        self.assertTrue(login)

        # give procurement officer permission to the user
        self.provide_permission_to_user(permission_group=permission_group, user=user)

        # Perform a request to the provided URL
        request = self.client.get(url)

        # Check permission status based on has_permission flag
        if has_permission:
            if self.client.request == "get":
                self.assertSuccess(request)
        else:
            if self.client.request == "get":
                self.assertPermissionDenied(request)

        # Clear the permission cache for the user and permission group
        self.clear_permission_cache(permission_group=permission_group, user=user)
        # Logout from the client
        self.client.logout()


    def check_with_different_permissions(
        self, available_permissions, user, url, unallowed_permissions=[]
    ):
        """
        Check requests with different permissions for a given user and URL.

        Args:
        - available_permissions (list): List of available permissions to be checked.
        - user (User): The user for whom permissions are being checked.
        - url (str): The URL to perform the requests.
        - unallowed_permissions (list, optional): List of permissions not allowed (default: []).

        Returns:
        - None
        """
        # Check permissions in the available_permissions list
        for permission in available_permissions:
            self.perform_request_with_permission(
                permission_group=permission, user=user, url=url, has_permission=True
            )

        # Check permissions in the unallowed_permissions list if provided
        if unallowed_permissions:
            for permission in unallowed_permissions:
                self.perform_request_with_permission(
                    permission_group=permission, user=user, url=url, has_permission=False
                )


    def assertCreated(self, request):
        self.assertEqual(request.status_code, 201)

    def assertSuccess(self, request):
        self.assertEqual(request.status_code, 200)

    def assertDeleted(self, request):
        self.assertEqual(request.status_code, 204)

    def assertBadRequest(self, request):
        self.assertEqual(request.status_code, 400)

    def assertPermissionDenied(self, request):
        self.assertEqual(request.status_code, 403)

    def assertNotFound(self, request):
        self.assertEqual(request.status_code, 404)

    def assertMethodNotAllowed(self, request):
        self.assertEqual(request.status_code, 405)

    def create_image(self, size=(50, 50)):
        file_ = BytesIO()
        image = Image.new('RGBA', size=size, color=(155, 0, 0))
        image.save(file_, 'png')
        file_.seek(0)
        mock_image = SimpleUploadedFile(
            name='test_image.png', content=file_.read(), content_type='image/png')
        return mock_image
