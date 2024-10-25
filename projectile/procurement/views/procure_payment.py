"""Views for Procure Payment related models."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView

from common.enums import Status

from core.views.common_view import (
    ListCreateAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
    CreateAPICustomView
)

from procurement.filters import ProcurePaymentFilter

from procurement.models import ProcurePayment, Procure

from core.permissions import (
    CheckAnyPermission,
    IsSuperUser,
    StaffIsAdmin,
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator,
    StaffIsProcurementOfficer,
    StaffIsDistributionT1,
)
from core.custom_serializer.person import PersonModelSerializer

from procurement.serializers.procure_payment import ProcurePaymentModelSerializer
from procurement.utils import calculate_procure_payment_data, get_updated_by_data


class ProcurePaymentList(ListCreateAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsProcurementOfficer,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    filterset_class = ProcurePaymentFilter

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProcurePaymentModelSerializer.List
        else:
            return ProcurePaymentModelSerializer.Post

    def get_queryset(self, related_fields=None, only_fields=None):
        queryset = ProcurePayment().get_all_actives().select_related("procure")

        return queryset


class BulkCreateProcurePaymentView(CreateAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsProcurementOfficer,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProcurePaymentModelSerializer.Post

    def create(self, request, *args, **kwargs):
        data = request.data

        # Ensure that the request data is a list
        if not isinstance(data, list):
            return Response(
                {"detail": "Invalid payload format. Expected a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Serialize each item in the list and perform validation
        serializer = self.get_serializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)

        # Perform bulk creation
        procure_payments = serializer.save()

        return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)


class ProcurePaymentDetail(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsProcurementOfficer,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    lookup_field = "alias"

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProcurePaymentModelSerializer.Detail
        else:
            return ProcurePaymentModelSerializer.Post

    def get_queryset(self, related_fields=None, only_fields=None):
        queryset = ProcurePayment().get_all_actives().select_related("procure")
        return queryset

    def perform_destroy(self, instance):
        instance.status = Status.INACTIVE
        instance.save(update_fields=["status"])
        calculate_procure_payment_data(instance.procure)


class ProcurePaymentLog(RetrieveAPIView):
    queryset = Procure.objects.all()
    lookup_field = "alias"

    def get(self, request, *args, **kwargs):
        # TODO: find a better solution to handle it without nested loop and with DRY
        instance = self.get_object().id
        payment_instances = ProcurePayment.objects.filter(procure_id=instance)

        history_data = []
        for procure_instance in payment_instances:
            history = list(procure_instance.history.all())
            for record in history:
                record_data = {
                    "date": record.history_date,
                    "type": record.get_history_type_display(),
                    "changed_by": f"{record.history_user.first_name} {record.history_user.last_name}",
                    "amount": {
                        "current": record.amount,
                        "previous": record.prev_record.amount
                        if record.prev_record
                        else "",
                    },
                    "method": {
                        "current": record.method,
                        "previous": record.prev_record.method
                        if record.prev_record
                        else "",
                    },
                    "method_reference": {
                        "current": record.method_reference,
                        "previous": record.prev_record.method_reference
                        if record.prev_record
                        else "",
                    },
                    "status": {
                        "current": record.status,
                        "previous": record.prev_record.status
                        if record.prev_record
                        else "",
                    },
                }
                history_data.append(record_data)

        return Response(history_data, status=status.HTTP_200_OK)
