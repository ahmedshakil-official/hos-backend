from rest_framework.response import Response
from rest_framework.views import APIView

from core.views.common_view import (
    ListAPICustomView,
    RetrieveUpdateDestroyAPICustomView
)
from core.models import (
    EmployeeManager
)
from core.custom_serializer.employee_manager import (
    EmployeeManagerModelSerializer
)
from ..filters import EmployeeManagerListFilter
from ..permissions import (
    StaffIsAdmin,
    CheckAnyPermission,
    StaffIsSalesManager,

)


class EmployeeManagerList(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsSalesManager,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = EmployeeManagerModelSerializer.List
    filterset_class = EmployeeManagerListFilter

    def get_queryset(self):
        return EmployeeManager.objects.select_related(
            'employee',
            'manager',
        ).filter().order_by('-id')


class EmployeeManagerDetails(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)
    lookup_field = 'alias'
    serializer_class = EmployeeManagerModelSerializer.Details

    def get_queryset(self):
        return EmployeeManager.objects.select_related(
            'employee',
            'manager',
        ).filter().order_by('-id')


class GetManagerByEmployeeCode(APIView):
    """
    Params:
        employee_code: str

    Returns:
        manager_code: str
    """
    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request, *args, **kwargs):
        employee_code = request.GET.get('employee_code')
        employee_manager = EmployeeManager().get_all_actives().filter(
            employee__code=employee_code
        ).values_list('manager__code', flat=True).first()
        return Response({
            'manager_code': employee_manager
        })
