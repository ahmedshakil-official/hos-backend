from datetime import datetime

from django.db.models import Prefetch, F, Subquery, OuterRef
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.enums import Status
from  common.utils import string_to_bool
from common.pagination import  CachedCountPageNumberPagination
from core.models import PersonOrganization

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
    StaffIsDeliveryMan,
    StaffIsProcurementOfficer,
    StaffCanEditProcurementWorseRateEdit,
    StaffIsProcurementBuyerWithSupplier,
    StaffIsDistributionT1,
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator,
)

from procurement.serializers.prediction_item import PredictionItemModelSerializer
from procurement.models import (
    PredictionItem,
    PredictionItemSupplier,
    PurchasePrediction,
    Procure,
)


class PredictionItemList(ListAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementBuyerWithSupplier,
        StaffIsDistributionT1,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission, )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PredictionItemModelSerializer.List
        return PredictionItemModelSerializer.List

    def get_queryset(self):
        supplier = self.request.query_params.get('supplier', None)
        purchase_prediction = self.request.query_params.get('purchase_prediction', None)
        if not supplier or not purchase_prediction:
            return PredictionItem.objects.none()
        self_assigned = string_to_bool(
            self.request.GET.get('self_assigned', None))
        team = string_to_bool(
            self.request.GET.get('team', None))
        # try:
        #     prediction_instance = PurchasePrediction.objects.only('id',).filter(
        #         status=Status.ACTIVE,
        #     ).last()
        #     prediction_instance_id = prediction_instance.id
        # except:
        #     return PredictionItem.objects.none()

        item_suppliers = PredictionItemSupplier.objects.filter(
            status=Status.ACTIVE,
            organization__id=self.request.user.organization_id,
            supplier__alias=str(supplier),
        ).order_by('-id')

        queryset = PredictionItem.objects.prefetch_related(
            Prefetch('prediction_item_suggestions', queryset=item_suppliers),
        ).filter(
            status=Status.ACTIVE,
            organization__id=self.request.user.organization_id,
            purchase_prediction__alias=purchase_prediction,
            purchase_order__lt=F('suggested_purchase_quantity')
        )
        if self_assigned:
            queryset = queryset.filter(
                assign_to=self.request.user.get_person_organization_for_employee(only_fields=['id'])
            )
        if team:
            pred_item = queryset.filter(
                assign_to=self.request.user.get_person_organization_for_employee(only_fields=['id']),
                team__isnull=False
            ).order_by('-id')[:1]
            if pred_item.exists():
                team_name = pred_item.first().team
                queryset = queryset.filter(team=team_name)
            else:
                return PredictionItem.objects.none()
        queryset = queryset.annotate(
            priority=Subquery(
                item_suppliers.filter(prediction_item=OuterRef('pk'), supplier__alias=str(supplier))
                .values('priority')
            )
        ).order_by('priority', 'company_name', 'product_name',)
        return queryset


class DownloadPredictionData(APIView):
    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )

    def get(self, request, *args, **kwargs):
        date = self.request.query_params.get('date', datetime.today().strftime('%Y-%m-%d'))
        min_days = self.request.query_params.get('min_days', 0)
        max_days = self.request.query_params.get('max_days', 0)
        available_balance = self.request.query_params.get('available_balance', 0)

        return Response(status=status.HTTP_200_OK)


class PredictionItemDetails(RetrieveUpdateDestroyAPICustomView):
    lookup_field = 'alias'
    queryset = PredictionItem.objects.filter(
        status=Status.ACTIVE
    )
    available_permission_classes = ()
    serializer_class = PredictionItemModelSerializer.WithWorstRate

    def get_permissions(self):
        if self.request.method == 'PATCH' or self.request.method == 'PUT':
            self.available_permission_classes = (
                IsSuperUser,
                StaffCanEditProcurementWorseRateEdit,
            )
        else:
            self.available_permission_classes = (
                StaffIsAdmin
            )
        return (CheckAnyPermission(),)


class GetInvoiceNumberForProcure(APIView):
    available_permission_classes = (
        StaffIsAdmin,
        IsSuperUser,
        StaffIsProcurementOfficer,
        StaffIsProcurementBuyerWithSupplier,
        StaffIsDistributionT1,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission, )

    def get(self, request, *args, **kwargs):
        user = self.request.user
        # TODO: Need to change this to Person Instead of PersonOrganization
        # We did this because there are some mismatch between Person and PersonOrganization name and code
        employee_code = user.get_full_name_initial_or_code_from_person_organization()
        procures = Procure.objects.filter(
            date__date=datetime.today().date(),
            status=Status.ACTIVE,
            employee__person__id=user.id,
        )
        total_procure_count = procures.count()

        invoice_number = f'{employee_code}_{total_procure_count + 1}'
        return Response(data={'invoice_number': invoice_number}, status=status.HTTP_200_OK)
