from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from common.enums import Status
from core.permissions import (
    CheckAnyPermission,
    IsSuperUser,
    StaffIsAdmin,
    AnyLoggedInUser,
    StaffIsProcurementOfficer,
    StaffIsProcurementBuyerWithSupplier,
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator,
    StaffIsDistributionT1,
)

from ..models import Procure

class ProcurementShopList(APIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementBuyerWithSupplier,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission, )

    def get(self, request):
        try:
            keyword = self.request.query_params.get('keyword', None)
            procure_shops = Procure.objects.filter(
                status=Status.ACTIVE,
                shop_name__isnull=False
            ).values_list('shop_name', flat=True)
            if keyword:
                procure_shops = procure_shops.filter(
                    shop_name__icontains=keyword
                )
            return Response(set(sorted(procure_shops)), status=status.HTTP_200_OK)
        except Exception as exception:
            return Response({"message": "Failed"}, status=status.HTTP_400_BAD_REQUEST)
