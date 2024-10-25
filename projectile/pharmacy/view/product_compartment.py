from core.views.common_view import ListCreateAPICustomView

from core.permissions import (
    StaffIsAdmin,
    StaffIsProcurementOfficer,
    CheckAnyPermission,
    StaffIsDistributionT1,
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator
)

from pharmacy.custom_serializer.product_compartment import ProductCompartmentModelSerializer

class ProductCompartmentList(ListCreateAPICustomView):
    serializer_class = ProductCompartmentModelSerializer.Link
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsDistributionT1,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission, )
