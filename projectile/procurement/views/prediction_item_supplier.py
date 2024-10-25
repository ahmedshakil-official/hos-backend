from weakref import finalize
from rest_framework.response import Response
from rest_framework import status

from common.enums import Status, ActionType
from common.helpers import change_key_mappings
from common.pagination import CachedCountPageNumberPagination

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
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator,
    StaffIsDistributionT1,
)
from procurement.serializers.prediction_item_supplier import PredictionItemSupplierModelSerializer
from procurement.serializers.prediction_item_mark import PredictionItemMarkModelSerializer
from procurement.serializers.procure_issue_log import ProcureIssueLogModelSerializer
from ..models import PredictionItem, PredictionItemMark, ProcureIssueLog


class PredictionItemSupplierInfo(ListAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = PredictionItemSupplierModelSerializer.ListWithSupplier
    pagination_class = CachedCountPageNumberPagination

    def get_marked_log(self, prediction_item_alias):
        queryset =  PredictionItemMark().get_all_actives().filter(
            prediction_item__alias=prediction_item_alias,
        ).select_related(
            'supplier',
            'employee',
        ).order_by('id')
        return PredictionItemMarkModelSerializer.List(queryset, many=True).data

    def get_issue_log(self, prediction_item_alias):
        queryset =  ProcureIssueLog().get_all_actives().filter(
            prediction_item__alias=prediction_item_alias,
        ).select_related(
            'supplier',
            'employee',
        ).order_by('id')
        return ProcureIssueLogModelSerializer.Lite(queryset, many=True).data

    def get_supplier_list(self, prediction_item_alias):
        purchase_days = self.request.query_params.get('purchase_days', 90)
        key_mappings = {
            "purchase__person_organization_supplier_id" : "id",
            "purchase__person_organization_supplier__company_name": "name",
            "purchase__person_organization_supplier__phone": "phone"
        }

        if isinstance(purchase_days, int):
            purchase_days = purchase_days
        elif isinstance(purchase_days, str):
            purchase_days = int(purchase_days)
        else:
            purchase_days = 90
        try:
            return change_key_mappings(PredictionItem.objects.get(
                alias=prediction_item_alias
            ).get_suppliers_by_days(purchase_days), key_mappings)
        except:
            return []

    def get_queryset(self, related_fields=None, only_fields=None):
        prediction_item_alias = self.request.query_params.get('prediction_item', None)
        if prediction_item_alias:
            return super().get_queryset(related_fields=related_fields, only_fields=only_fields).select_related(
                'supplier',
            ).filter(prediction_item__alias=prediction_item_alias).order_by('priority')
        return super().get_queryset(related_fields=related_fields, only_fields=only_fields).select_related(
            'supplier',
        ).order_by('priority')

    def get_supplier_avg_rate(self, prediction_item_alias, supplier_alias):
        try:
            return PredictionItem.objects.only('id', 'stock_id').get(
                alias=prediction_item_alias
            ).get_supplier_avg_rate(supplier_alias)
        except:
            return None

    def get(self, request, *args, **kwargs):
        prediction_item_alias = self.request.query_params.get('prediction_item', None)
        supplier_alias = self.request.query_params.get('supplier_alias', None)
        finalize_response = self.finalize_response(request, response=self.list(request, *args, **kwargs)).data
        if prediction_item_alias:
            finalize_response = {
                "suggested_supplier_data": finalize_response.get('results', []),
                "marked_log": self.get_marked_log(prediction_item_alias),
                "issue_log": self.get_issue_log(prediction_item_alias),
                "suppliers": self.get_supplier_list(prediction_item_alias),
                "supplier_avg_rate": self.get_supplier_avg_rate(prediction_item_alias, supplier_alias)
            }
        return Response(finalize_response, status=status.HTTP_200_OK)
