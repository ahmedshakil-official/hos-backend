from rest_framework import permissions
from rest_framework.permissions import BasePermission
from common.enums import (
    PublishStatus,
    Status,
)
from core.enums import PersonGroupType
from core.models import (
    PersonOrganization,
    GroupPermission,
    PersonOrganizationGroupPermission,
)

class IsAuthenticatedOrCreate(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if request.method == 'POST':
            return True
        return super(IsAuthenticatedOrCreate, self).has_permission(request, view)


class IsOwnerOrReadOnly(permissions.IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.organization_id == request.user.organization_id


class IsOwner(permissions.IsAuthenticated):

    def has_object_permission(self, request, view, obj):
        return obj.organization_id == request.user.organization_id


class IsOwnerOrSuperUserOrReadOnly(permissions.IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_superuser:
            return True

        return obj.organization_id == request.user.organization_id


class IsOwnerAndAdmin(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        return request.user.is_staff

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return obj.organization_id == request.user.organization_id

        return False


class IsOwnerAndAdminOrGlobal(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        return request.user.is_staff

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            if obj.is_global in [PublishStatus.INITIALLY_GLOBAL, PublishStatus.WAS_PRIVATE_NOW_GLOBAL]:
                return True
            elif obj.organization_id == request.user.organization_id:
                return True

        return False


class IsSuperUserOrReadOnly(permissions.IsAuthenticatedOrReadOnly):

    def has_permission(self, request, view):
        return request.user.is_superuser

    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_superuser:
            return True

        return False


class IsSuperUser(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        return request.user.is_superuser

    def has_object_permission(self, request, view, obj):

        if request.user.is_superuser:
            return True

        return False


class CheckAnyPermission(BasePermission):

    def get_permissions(self, view):

        # Get all permissions

        _permissions = getattr(view, "available_permission_classes", [])

        if not hasattr(_permissions, "__iter__"):
            # Available_permission_classes contain only one permission
            return [_permissions]

        # Already a list
        return _permissions

    def has_permission(self, request, view):

        # Fetching all permission class name, from `available_permission_classes` variable
        _permissions = self.get_permissions(view)

        if not _permissions:
            # Does not contain any permission
            return False

        for perm_class in _permissions:

            if hasattr(perm_class, "__iter__"):
                # the current item of permissions class is iterable
                classes = perm_class
                permission_flag = False
                for _perm_class in classes:
                    # the current item of permissions class is iterable
                    permission = _perm_class()

                    if permission.has_permission(request, view):
                        permission_flag = True
                        break
                    else:
                        pass

                if permission_flag:
                    return True
            else:

                # the current item of permissions class is not iterable
                permission = perm_class()

                if permission.has_permission(request, view):
                    return True
                else:
                    pass

        return False

    def has_object_permission(self, request, view, obj):
        """
        Check the object permissions on the view.
        """

        _permissions = self.get_permissions(view)

        if not _permissions:
            return False

        for perm_class in _permissions:
            if hasattr(perm_class, "__iter__"):
                classes = perm_class

                permission_flag = False
                for _perm_class in classes:
                    permission = _perm_class()
                    if permission.has_object_permission(request, view, obj):
                        permission_flag = True
                        break
                if permission_flag:
                    return True
            else:
                permission = perm_class()

                if permission.has_object_permission(request, view, obj):
                    return True
        return False


class IsLoggedInOnOrganization(permissions.IsAuthenticated):
    def __init__(self, group):
        # assigning group name, E.G. Accounts, Nurse. Note that,
        # this name must exist on GroupPermission Table
        self.group_name = group

    def has_permission(self, request, view):

        if not hasattr(request.user, 'organization_id'):
            return False

        if self.group_name == 'Public' or (self.group_name == 'Admin' and (request.user.is_staff or request.user.is_superuser)):
            return True

        return request.user.does_belongs_to_group_or_admin(self.group_name)

    def has_object_permission(self, request, view, obj):
        allowed_for_all_views_list = [
            'DistributorStockDetails'
        ]
        if view.__class__.__name__ in allowed_for_all_views_list and request.method == 'GET':
            return True

        if hasattr(request.user, 'organization_id'):
            # HealthOS org id is 303, allowing permission for all HealthOs users
            if request.user.organization_id == 303:
                return True

        if hasattr(obj, 'is_global'):
            if obj.is_global in [PublishStatus.INITIALLY_GLOBAL, PublishStatus.WAS_PRIVATE_NOW_GLOBAL]:
                return request.user.is_superuser or request.method == 'GET'
            elif obj.is_global == PublishStatus.PRIVATE and hasattr(obj, 'organization_id'):
                return obj.organization_id == request.user.organization_id

        elif hasattr(obj, 'organization_id') and not hasattr(obj, 'distributor_id'):
            if obj.organization_id == request.user.organization_id:
                return True

        elif hasattr(obj, 'distributor_id') and hasattr(obj, 'organization_id'):
            if obj.distributor_id == request.user.organization_id or obj.organization_id ==\
                request.user.organization_id:
                return True
        else:
            return True
        return False


class StaffIsAccountant(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsAccountant, self).__init__('Accounts')


class StaffIsAdmin(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsAdmin, self).__init__('Admin')


class UserIsPatient(IsLoggedInOnOrganization):
    def __init__(self):
        super(UserIsPatient, self).__init__('Patient')


class StaffIsPhysician(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsPhysician, self).__init__('Physician')


class StaffIsNurse(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsNurse, self).__init__('Nurse')


# class StaffIsProcurementOfficer(IsLoggedInOnOrganization):
#     def __init__(self):
#         super(StaffIsProcurementOfficer, self).__init__('Procurement')


class StaffIsLaboratoryInCharge(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsLaboratoryInCharge, self).__init__('Laboratory')


class StaffIsSalesman(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsSalesman, self).__init__('Salesman')


class StaffIsSalesReturn(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsSalesReturn, self).__init__('SalesReturn')


class StaffIsAdjustment(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsAdjustment, self).__init__('Adjustment')


class StaffIsReceptionist(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsReceptionist, self).__init__('General')

class StaffIsMonitor(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsMonitor, self).__init__('Monitor')

class StaffIsDeliveryMan(IsLoggedInOnOrganization):
    def __init__(self):
        super().__init__('DeliveryMan')

class AnyLoggedInUser(IsLoggedInOnOrganization):
    def __init__(self):
        super(AnyLoggedInUser, self).__init__('Public')


class StaffIsTrader(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        if (request.method in permissions.SAFE_METHODS or request.method == 'POST') and \
            hasattr(request.user, 'person_group'):
            return request.user.person_group == \
                PersonGroupType.TRADER and request.user.status == Status.ACTIVE
        return False

    def has_object_permission(self, request, view, obj):
        if request.method == 'POST':
            return True
        return obj.entry_by_id == request.user.id


class StaffIsContactor(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        if (request.method in permissions.SAFE_METHODS or request.method == 'POST') and \
            hasattr(request.user, 'person_group'):
            return request.user.person_group == \
                PersonGroupType.CONTRACTOR and request.user.status == Status.ACTIVE
        return False

    def has_object_permission(self, request, view, obj):
        return True if request.method == 'POST' else obj.entry_by_id == request.user.id



class StaffCanEditProcurementWorseRateEdit(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffCanEditProcurementWorseRateEdit, self).__init__('PredictionItemWorstRateEdit')


class StaffIsTelemarketer(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsTelemarketer, self).__init__('TeleMarketing')

class StaffIsProcurementBuyerWithSupplier(IsLoggedInOnOrganization):
    def __init__(self):
        super().__init__('Procurement')

    def has_permission(self, request, view):

        if not hasattr(request.user, 'organization_id'):
            return False

        if self.group_name == 'Public' or (self.group_name == 'Admin' and request.user.is_staff):
            return True

        return request.user.does_belongs_to_group_or_admin(self.group_name) and request.user.has_tagged_supplier


class StaffIsProcurementOfficer(IsLoggedInOnOrganization):
    def __init__(self):
        super().__init__('Procurement')

    def has_permission(self, request, view):

        if not hasattr(request.user, 'organization_id'):
            return False

        if self.group_name == 'Public' or (self.group_name == 'Admin' and request.user.is_staff):
            return True

        return request.user.does_belongs_to_group_or_admin(self.group_name) and not request.user.has_tagged_supplier


class StaffIsMarketer(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsMarketer, self).__init__("Marketing")


class StaffIsDeliveryHub(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsDeliveryHub, self).__init__("DeliveryHub")


class StaffIsDistributionT1(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsDistributionT1, self).__init__("Distribution T1")


class StaffIsDistributionT2(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsDistributionT2, self).__init__("Distribution T2")


class StaffIsDistributionT3(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsDistributionT3, self).__init__("Distribution T3")


class StaffIsFrontDeskProductReturn(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsFrontDeskProductReturn, self).__init__("Front Desk (Product Return)")


class StaffIsProcurementManager(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsProcurementManager, self).__init__("Procurement Manager")


class StaffIsSalesCoordinator(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsSalesCoordinator, self).__init__("Sales Coordinator")


class StaffIsSalesManager(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsSalesManager, self).__init__("Sales Manager")


class StaffIsProcurementCoordinator(IsLoggedInOnOrganization):
    def __init__(self):
        super(StaffIsProcurementCoordinator, self).__init__("Procurement Coordinator")