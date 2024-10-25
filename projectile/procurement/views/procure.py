import csv
from django.utils import timezone
from dateutil import parser
from django.db import transaction
from django.db.models import Prefetch
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    ListAPIView,
    RetrieveUpdateAPIView,
    UpdateAPIView,
    RetrieveAPIView,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.views import APIView

from common.enums import Status, ActionType
from common.pagination import CachedCountPageNumberPagination
from core.enums import PersonGroupType

from core.views.common_view import(
    ListCreateAPICustomView,
    CreateAPICustomView,
    ListAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
)
from core.permissions import (
    CheckAnyPermission,
    IsSuperUser,
    StaffIsAdmin,
    AnyLoggedInUser,
    StaffIsProcurementOfficer,
    StaffIsProcurementBuyerWithSupplier,
    StaffIsContactor,
    StaffIsDistributionT1,
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator,
)
from procurement.serializers.procure import ProcureModelSerializer
from procurement.utils import get_procure_update_date, update_procures_credit
from ..models import (
    Procure,
    PurchasePrediction,
    ProcureGroup,
    ProcurePayment,
    PredictionItem,
    ProcureItem,
)
from ..filters import ProcureListFilter
from ..serializers.procure_item import ProcureItemModelSerializer
from ..enums import ProcureDateUpdateType


class ProcureListCreate(ListCreateAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementBuyerWithSupplier,
        StaffIsContactor,
        StaffIsDistributionT1,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission, )
    filterset_class = ProcureListFilter
    pagination_class = CachedCountPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProcureModelSerializer.List
        return ProcureModelSerializer.Post

    def get_queryset(self, related_fields=None, only_fields=None):
        user = self.request.user
        contractor_id = (user.get_person_organization_with_type(person_group_type=PersonGroupType.CONTRACTOR).id
                        if user.person_group == PersonGroupType.CONTRACTOR else None)
        # If User is has tagged supplier, only return procurements for that supplier
        queryset = super().get_queryset(related_fields=related_fields, only_fields=only_fields).select_related(
            'supplier',
            'employee',
            'contractor',
            'procure_group',
        ).order_by('-date', '-id')

        if contractor_id:
            return queryset.filter(
                contractor__id=contractor_id
            )

        if user_tagged_supplier_id := user.tagged_supplier_id:
            person_organization_employee = user.get_person_organization_for_employee(
                only_fields=['id', ]
            )
            return queryset.filter(
                supplier__id=user_tagged_supplier_id,
                employee=person_organization_employee
            )

        elif not user.is_admin_or_super_admin_or_procurement_manager_or_procurement_coordinator():
            person_organization_employee_id = user.get_person_organization_for_employee(
                pk_only=True
            )
            return queryset.filter(
                employee__id=person_organization_employee_id
            )

        return queryset


class ProcureDetails(RetrieveUpdateDestroyAPICustomView):
    lookup_field = 'alias'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProcureModelSerializer.Details
        return ProcureModelSerializer.Post

    def get_queryset(self):
        payment_queryset = ProcurePayment().get_all_actives()
        return super().get_queryset().select_related(
            "supplier",
            "contractor",
            "employee",
        ).prefetch_related(
            Prefetch(
                "procure_payments", queryset=payment_queryset
            )
        )

    def get_permissions(self):
        if self.request.method == 'GET':
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsDistributionT1,
                StaffIsProcurementOfficer,
                StaffIsProcurementManager,
                StaffIsProcurementCoordinator,
                StaffIsProcurementBuyerWithSupplier,
            )
        else:
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsDistributionT1,
                StaffIsProcurementOfficer,
                StaffIsProcurementManager,
                StaffIsProcurementCoordinator
            )
        return (CheckAnyPermission(), )


class CompletePurchase(CreateAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProcureModelSerializer.ProcurePurchase

    @transaction.atomic
    def post(self, request, *args, **kwargs):

        try:
            with transaction.atomic():
                serializer = ProcureModelSerializer.ProcurePurchase(
                    data=request.data, context={'request': request})
                if serializer.is_valid(raise_exception=True):
                    procure = serializer.data.get('procure', '')
                    action = serializer.data.get('action', '')
                    date = serializer.data.get('date', '')
                    _date = parser.parse(date)
                    procure_instance = Procure.objects.get(pk=procure)
                    if action == ActionType.CREATE:
                        procure_instance.complete_purchase(
                            _date,
                            request.user.organization_id,
                            request.user,
                        )
                    elif action == ActionType.DELETE:
                        procure_instance.delete_related_purchase(
                            request.user.id,
                        )
                    response = {
                        'message': 'Success',
                    }
                    return Response(
                        response,
                        status=status.HTTP_201_CREATED
                    )

        except Exception as exception:
            exception_str = exception.args[0] if exception.args else str(exception)
            content = {'error': '{}'.format(exception_str)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class ProcureChangeLog(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    lookup_field = 'alias'
    serializer_class = ProcureItemModelSerializer.Lite

    def get(self, request, *args, **kwargs):
        from core.custom_serializer.person import PersonModelSerializer

        procure = Procure.objects.get(alias=self.kwargs.get('alias'))
        previous_instances = procure.get_all_previous_instances()
        all_items = []
        for instance in previous_instances:
            instance_items = instance.procure_items.all()
            all_items.append({
                'procure': instance.id,
                'created_at': instance.created_at,
                'entry_by': PersonModelSerializer.EntryBy(instance.entry_by).data,
                'sub_total': instance.sub_total,
                'discount': instance.discount,
                'current_status': instance.current_status,
                'invoices': instance.invoices,
                'total_items': instance_items.count(),
                'procure_items': self.serializer_class(instance_items, many=True).data,
            }
            )
        return Response(all_items, status=status.HTTP_200_OK)


class ProcureStatusLog(ListAPIView):
    lookup_field = 'alias'

    def get_queryset(self):
        return Procure.objects.filter(
            alias=self.kwargs.get('alias'),
            status=Status.ACTIVE
        )

    def get_permissions(self):
        if self.request.method == 'GET':
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsDistributionT1,
                StaffIsProcurementOfficer,
                StaffIsProcurementManager,
                StaffIsProcurementCoordinator,
                StaffIsProcurementBuyerWithSupplier,
            )
        else:
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsDistributionT1,
                StaffIsProcurementOfficer,
                StaffIsProcurementManager,
                StaffIsProcurementCoordinator
            )
        return (CheckAnyPermission(),)

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        history = list(instance.history.all())

        history_data = []
        for record in history:
            record_data = {
                "date": record.history_date,
                "type": record.get_history_type_display(),
                "changed_by": f"{record.history_user.first_name} {record.history_user.last_name}",
                "current_status": record.current_status,
                "previous_status": record.prev_record.current_status if record.prev_record else ""
            }
            history_data.append(record_data)

        return Response(history_data, status.HTTP_200_OK)


class ProcureGroupStatusLog(ListAPIView):
    lookup_field = 'alias'

    def get_queryset(self):
        return ProcureGroup.objects.filter(
            alias=self.kwargs.get('alias'),
            status=Status.ACTIVE,
            procure_group_procures__status=Status.ACTIVE,
            procure_group_procures__procure_items__status=Status.ACTIVE
        )

    def get_permissions(self):
        if self.request.method == 'GET':
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsDistributionT1,
                StaffIsProcurementOfficer,
                StaffIsProcurementManager,
                StaffIsProcurementCoordinator,
                StaffIsProcurementBuyerWithSupplier,
            )
        else:
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsDistributionT1,
                StaffIsProcurementOfficer,
                StaffIsProcurementManager,
                StaffIsProcurementCoordinator
            )
        return (CheckAnyPermission(),)

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        history = list(instance.history.all())

        history_data = []
        for record in history:
            record_data = {
                "date": record.history_date,
                "type": record.get_history_type_display(),
                "changed_by": f"{record.history_user.first_name} {record.history_user.last_name}",
                "current_status": record.current_status,
                "previous_status": record.prev_record.current_status if record.prev_record else ""
            }

            history_data.append(record_data)

        return Response(history_data, status.HTTP_200_OK)


class ProcureHistory(RetrieveAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsDistributionT1,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsProcurementBuyerWithSupplier,
    )
    lookup_field = "alias"
    permission_classes = (CheckAnyPermission,)
    queryset = Procure.objects.all()

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        history = list(instance.history.all())

        history_data = []

        for record in history:
            record_data = {
                "date": record.history_date, "type": record.get_history_type_display(),
                "changed_by": f"{record.history_user.first_name} {record.history_user.last_name}",

                "credit_amount": {
                    "current": record.credit_amount,
                    "previous": record.prev_record.credit_amount if record.prev_record else ""
                },

                "credit_payment_term": {
                    "current": record.credit_payment_term,
                    "previous": record.prev_record.credit_payment_term if record.prev_record else ""
                },

                "credit_cost_percentage": {
                    "current": record.credit_cost_percentage,
                    "previous": record.prev_record.credit_cost_percentage if record.prev_record else ""
                },

                "status": {
                    "current": record.current_status,
                    "previous": record.prev_record.current_status if record.prev_record else ""
                }
            }
            history_data.append(record_data)

        return Response(history_data, status=status.HTTP_200_OK)


class ProcureDateUpdate(APIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsDistributionT1,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsProcurementBuyerWithSupplier,
    )
    permission_classes = (CheckAnyPermission,)

    def post(self, request,  *args, **kwargs):
        # Get data from the request
        procure_alias = request.data.get('alias', '')
        is_confirmed: bool = request.data.get('is_confirmed', False)
        _type = request.data.get('type', None)

        # Check if procure_alias is provided
        if not procure_alias:
            return Response(
                {'detail': 'Procure alias is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if type is provided
        if not _type:
            return Response(
                {'detail': 'Procure date update type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if type is valid
        if not _type in ProcureDateUpdateType:
            return Response(
                { "detail": "Please provide a valid type" },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Attempt to retrieve a Procure object with the given alias
            procure = Procure().get_all_non_inactives().select_related("procure_group").get(
                alias=procure_alias
            )

        except Procure.DoesNotExist:
            # If Procure with the given alias does not exist, return a 404 response
            return Response(
                {'error': 'Procure not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if the created date and procure date are the same when advancing procure date
        if _type == ProcureDateUpdateType.ADVANCE and procure.created_at.date() != procure.date.date():
            return Response(
                {"detail": "Already advanced the purchase."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if the created date and procure date are not same when reversing advance procure date
        if _type == ProcureDateUpdateType.REVERSE_ADVANCE and procure.created_at.date() == procure.date.date():
            return Response(
                {"detail": "This purchase has no advance purchase to be reversed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        procure_update_date = get_procure_update_date(date=procure.date, date_update_type=_type)

        # Check if confirmation is requested
        if is_confirmed:
            if procure.procure_group_id:
                # If the procure is part of a group, update all procures in the group
                procures = Procure().get_all_non_inactives().filter(
                    procure_group_id=procure.procure_group_id
                )
                procures.update(date=procure_update_date)
                # Get the procure ids to update procure items
                procure_ids = procures.values_list("id", flat=True)
                procure.procure_group.date = procure_update_date
                procure.procure_group.save(update_fields=['date', ])

                # update the procures related procure items date
                ProcureItem().get_all_non_inactives().filter(
                    procure_id__in=procure_ids
                ).update(date=procure_update_date)

                return Response({
                    "detail": "Procure and procure group date updated successfully."
                }, status=status.HTTP_200_OK)
            else:
                # If the procure is not part of a group, update its date
                procure.date = procure_update_date
                procure.save(update_fields=['date', ])
                # Update procure items date
                procure.procure_items.update(date=procure_update_date)

                return Response({
                    "detail": "Procure date updated successfully."
                }, status=status.HTTP_200_OK)
        else:
            if procure.procure_group_id:
                # If confirmation is not requested and procure is part of a group, provide an error response
                procure_count = Procure().get_all_non_inactives().filter(
                    procure_group_id=procure.procure_group_id
                ).count()

                return Response({
                    "detail": f"Procure already grouped with {procure_count} procures."
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # If confirmation is not requested and procure is not part of a group, update its date
                procure.date = procure_update_date
                procure.save(update_fields=['date', ])

                # update the procure items date also
                procure.procure_items.update(date=procure_update_date)

                return Response({
                    "detail": "Procure date updated successfully."
                }, status=status.HTTP_200_OK)


class ProcureCreditBulkUpdate(APIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)

    def post(self, request):
        serializer = ProcureModelSerializer.ProcureCreditBulkUpdate(data=request.data)

        if serializer.is_valid():
            update_procures_credit(serializer.validated_data)
            response = {"message": "Success"}
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
