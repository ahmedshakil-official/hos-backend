import csv
from decimal import Decimal

from django.core.cache import cache
from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg
from django.db import transaction
from django.db.models import Value, F, IntegerField, CharField, JSONField, Sum, Prefetch, Count, When, Case, Func, Q, DecimalField
from django.db.models.functions import Concat, Cast, Coalesce
from rest_framework import status
from rest_framework.response import Response
from django.utils.translation import gettext as _

from common.cache_keys import PURCHASE_REQUISITION_CREATE_REQUEST_CACHE_KEY
from common.enums import Status, ActionType
from common.pagination import CachedCountPageNumberPagination
from core.permissions import (
    StaffIsAdmin,
    StaffIsProcurementOfficer,
    CheckAnyPermission,
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator,
    StaffIsDistributionT1,
)
from core.views.common_view import ListCreateAPICustomView, RetrieveUpdateDestroyAPICustomView, CreateAPICustomView, ListAPICustomView
from pharmacy.helpers import get_product_short_name
from pharmacy.models import Stock
from procurement.filters import ProcureGroupListFilter, ProcureInfoReportFilter
from procurement.models import ProcureGroup, ProcureItem, Procure
from procurement.serializers.procure_group import ProcureGroupModelSerializer
from procurement.utils import generate_credit_report_csv_response


class ProcureGroupListCreate(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    filterset_class = ProcureGroupListFilter
    pagination_class = CachedCountPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProcureGroupModelSerializer.List
        return ProcureGroupModelSerializer.Post

    def get_queryset(self):
        procures = Procure().get_all_actives()
        queryset = ProcureGroup.objects.filter(
            status=Status.ACTIVE,
            procure_group_procures__status=Status.ACTIVE,
            procure_group_procures__procure_items__status=Status.ACTIVE
        ).prefetch_related(
        Prefetch(
            "procure_group_procures",
            queryset=procures,
        )
        ).select_related(
            "supplier",
            "contractor",
        ).annotate(
            invoices=JSONBAgg(F("procure_group_procures__invoices"), distinct=True),
            total_credit_amount = Coalesce(
                F("credit_amount") + Sum("procure_group_procures__credit_amount"),
            0.00, output_field=DecimalField()),
            total_paid_amount = Coalesce(
                F("paid_amount") + Sum("procure_group_procures__paid_amount"),
            0.00, output_field=DecimalField()),
            total_open_credit_balance = F("total_credit_amount") + F("credit_cost_amount") - F("total_paid_amount"),
        ).order_by("-pk")

        return queryset


    def post(self, request, *args, **kwargs):
        serializer = ProcureGroupModelSerializer.Post(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid(raise_exception=True):
            created_procure_groups, procure_could_not_be_grouped = serializer.save()
            if len(procure_could_not_be_grouped) > 0:
                return Response({
                    "detail": _("SOME_PROCURES_COULD_NOT_BE_GROUPED_AS_THEY_ARE_IN_DIFFERENT_STATUS"),
                    "procures": procure_could_not_be_grouped
                }, status=status.HTTP_409_CONFLICT)
            elif len(created_procure_groups) > 0:
                procure_groups = ProcureGroupModelSerializer.List(
                    created_procure_groups,
                    many=True,
                    context={'request': request}
                )
                return Response({
                    "message": "Success",
                    "results": procure_groups.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "detail": _("NO_PROCURES_FOUND_TO_CREATE_PROCURE_GROUP"),
            }, status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ProcureGroupDetails(RetrieveUpdateDestroyAPICustomView):

    def get_permissions(self):
        if self.request.method == 'DELETE':
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsProcurementManager,
                StaffIsProcurementCoordinator,
                StaffIsDistributionT1,
            )
        else:
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsProcurementOfficer,
                StaffIsProcurementManager,
                StaffIsProcurementCoordinator,
                StaffIsDistributionT1,
            )
        return (CheckAnyPermission(),)
    lookup_field = 'alias'

    def get_queryset(self):
        queryset = ProcureGroup.objects.filter(
            alias=self.kwargs.get('alias'),
            status=Status.ACTIVE,
            procure_group_procures__status=Status.ACTIVE,
            procure_group_procures__procure_items__status=Status.ACTIVE
        ).select_related(
            'supplier',
        ).annotate(
            invoices=ArrayAgg(F('procure_group_procures__invoices'), distinct=True),
            employees=ArrayAgg(
                Concat(
                    Value('{'),
                    Value('"id": '),
                    Cast(F('procure_group_procures__employee__id'), IntegerField()),
                    Value(', "alias": "'),
                    Cast(F('procure_group_procures__employee__alias'), CharField()),
                    Value('", "first_name": "'),
                    Cast(F('procure_group_procures__employee__first_name'), CharField()),
                    Value('", "last_name": "'),
                    Cast(F('procure_group_procures__employee__last_name'), CharField()),
                    Value('", "company_name": "'),
                    Cast(F('procure_group_procures__employee__company_name'), CharField()),
                    Value('"}'),
                    delimiter='',
                    output_field=JSONField()
                ),
                distinct=True,
            ),
            total_credit_amount = Coalesce(
                F("credit_amount") + Sum("procure_group_procures__credit_amount"),
            0.00, output_field=DecimalField()),
            total_paid_amount = Coalesce(
                F("paid_amount") + Sum("procure_group_procures__paid_amount"),
            0.00, output_field=DecimalField()),
            total_open_credit_balance = F("total_credit_amount") + F("credit_cost_amount") - F("total_paid_amount"),
        ).order_by('-pk')

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProcureGroupModelSerializer.Details
        else:
            return ProcureGroupModelSerializer.Update


class ProcureGroupStatusChange(CreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementCoordinator,
        StaffIsProcurementManager,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProcureGroupModelSerializer.StatusChange


class ProcureGroupCompletePurchase(CreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProcureGroupModelSerializer.CompletePurchase

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # Get the alias from the request data
        procure_group_alias = request.data.get("alias", "")
        # Create a cache key for the purchase requisition create request
        cache_key = PURCHASE_REQUISITION_CREATE_REQUEST_CACHE_KEY + procure_group_alias
        # Check if an existing request is in the cache
        existing_request = cache.get(cache_key)
        if existing_request:
            # If there's an existing request, return a response with message
            return Response(
                {
                    "detail": "Purchase requisition create request for the procure group is already running"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set a cache entry to mark the requisition creation request is in progress
        cache_data:bool = True
        # Set cache timeout to 5 min
        cache.set(cache_key, cache_data, 300)

        try:
            with transaction.atomic():
                serializer = ProcureGroupModelSerializer.CompletePurchase(
                    data=request.data,
                    context={'request': request}
                )
                if serializer.is_valid(raise_exception=True):
                    alias = serializer.validated_data.get('alias')
                    action = serializer.validated_data.get('action')
                    _date = serializer.validated_data.get('date')
                    procure_group = ProcureGroup.objects.filter(
                        alias=alias,
                    )
                    if procure_group.exists():
                        procure_group = procure_group.first()
                        if action == ActionType.CREATE:
                            procure_group.complete_group_purchase(
                                _date,
                                request.user.organization_id,
                                request.user,
                            )
                        elif action == ActionType.DELETE:
                            procure_group.delete_related_purchase_from_procure_group(
                                request.user.id,
                            )
                    # delete the requisition create request cached data
                    cache.delete(cache_key)

                    return Response({
                        'detail': _('SUCCESS'),
                    }, status=status.HTTP_200_OK)
                return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as exception:
            # delete the requisition create request cached data
            cache.delete(cache_key)
            exception_str = exception.args[0] if exception.args else str(exception)
            content = {'detail': '{}'.format(exception_str)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class ProcureGroupEdit(CreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProcureGroupModelSerializer.ProcuresEdit

    def post(self, request, *args, **kwargs):
        serializer = ProcureGroupModelSerializer.ProcuresEdit(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid(raise_exception=True):
            try:
                with transaction.atomic():
                    alias = serializer.data.get('alias')
                    procure_procure_items = serializer.data.get('procures')
                    stock_ids = []

                    for item in procure_procure_items:
                        stock = item.get('stock')
                        stock_ids.append(stock)
                        quantity = Decimal(item.get('quantity'))
                        rate = Decimal(item.get('rate'))
                        procure_items = ProcureItem.objects.filter(
                            procure__procure_group__alias=alias,
                            stock=stock,
                            rate=rate,
                            status=Status.ACTIVE
                        ).order_by('-date')
                        # Get total suggested quantity from the Prediction File associated with the Procure Items
                        total_suggested_quantity = procure_items.aggregate(
                            total_quantity=Coalesce(
                                Sum('prediction_item__suggested_purchase_quantity', distinct='prediction_item__id'),
                                0,
                                output_field=IntegerField()
                            )
                        ).get('total_quantity')
                        total_purchase_order = procure_items.aggregate(
                            total_quantity=Coalesce(
                                Sum('prediction_item__purchase_order', distinct='prediction_item__id'),
                                0,
                                output_field=IntegerField()
                            )
                        ).get('total_quantity')
                        total_purchase_quantity = procure_items.aggregate(
                            total_quantity=Coalesce(
                                Sum('quantity', distinct="id"),
                                0,
                                output_field=IntegerField()
                            )
                        ).get('total_quantity')
                        allow_over_purchase = request.user.has_permission_for_procurement_over_purchase()
                        valid_quantity = (total_suggested_quantity - total_purchase_order) + total_purchase_quantity
                        if quantity > valid_quantity and not allow_over_purchase:
                            product_full_name = get_product_short_name(
                                Stock.objects.get(id=stock).product
                            )
                            raise Exception(f'Purchase quantity can\'t be greater than suggested quantity for {product_full_name}. It must be less or equal {valid_quantity}.')

                        # Get Total Quantity of the Procure Items
                        total_quantity = procure_items.aggregate(
                            total_quantity=Coalesce(Sum('quantity'), 0, output_field=IntegerField())).get(
                            'total_quantity')
                        if quantity < total_quantity:
                            quantity_deducted = total_quantity - quantity
                            for procure_item in procure_items:
                                # If the quantity is greater than the quantity of the procure item
                                # then set the  status to inactive
                                # Else clone the procure_item with the new quantity
                                if quantity_deducted >= procure_item.quantity:
                                    quantity_deducted = quantity_deducted - procure_item.quantity
                                    procure_item.status = Status.INACTIVE
                                    procure_item.save(update_fields=['status'])
                                else:
                                    new_quantity = procure_item.quantity - quantity_deducted
                                    procure_item.clone_procure_item_with_new_quantity(
                                        new_quantity,
                                        request
                                    )
                                    break
                        elif quantity > total_quantity:
                            procure_item = procure_items.first()
                            quantity_added = quantity - total_quantity
                            new_quantity = procure_item.quantity + quantity_added
                            procure_item.clone_procure_item_with_new_quantity(
                                new_quantity,
                                request
                            )
                        else:
                            continue
                    procures = Procure.objects.filter(
                        procure_group__alias=alias,
                        status=Status.ACTIVE,
                        procure_items__stock__id__in=stock_ids
                    ).distinct('id')

                    for procure in procures:
                        procure.clone_procure_with_updated_subtotal(
                            request
                        )

                    procure_group = ProcureGroup.objects.get(alias=alias).update_group_stats()
                    serializer = ProcureGroupModelSerializer.Details(
                        procure_group,
                        context={'request': request}
                    )
                    return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as exception:
                exception_str = exception.args[0] if exception.args else str(exception)
                content = {'detail': '{}'.format(exception_str)}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ProcureInfoReport(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProcureGroupModelSerializer.ProcureInfoReport
    filterset_class = ProcureInfoReportFilter
    pagination_class = CachedCountPageNumberPagination

    def get_queryset(self):
        procures = Procure().get_all_actives()
        queryset = ProcureGroup.objects.filter(
            status=Status.ACTIVE,
            procure_group_procures__status=Status.ACTIVE,
            procure_group_procures__procure_items__status=Status.ACTIVE
        ).prefetch_related(
        Prefetch(
            "procure_group_procures",
            queryset=procures,
        )
        ).select_related(
            "supplier",
            "contractor",
        ).annotate(
            invoices=JSONBAgg(F("procure_group_procures__invoices"), distinct=True),
            total_credit_amount = Coalesce(
                F("credit_amount") + Sum("procure_group_procures__credit_amount"),
            0.00, output_field=DecimalField()),
            total_paid_amount = Coalesce(
                F("paid_amount") + Sum("procure_group_procures__paid_amount"),
            0.00, output_field=DecimalField()),
            total_open_credit_balance = F("total_credit_amount") - F("total_paid_amount"),
        ).order_by("-pk")

        return queryset

    def get(self, request, *args, **kwargs):
        is_csv_download = self.request.query_params.get("csv_download", None)
        if is_csv_download:
            queryset = self.get_queryset()
            filters = {
                "date__gte": self.request.query_params.get("date_0"),
                "date__lte": self.request.query_params.get("date_1"),
                "credit_payment_term_date__exact": self.request.query_params.get("credit_payment_term_date"),
                "supplier__exact": self.request.query_params.get("supplier"),
                "credit_status__exact": self.request.query_params.get("credit_status"),
            }

            for key, value in filters.items():
                if value:
                    queryset = queryset.filter(**{key: value})

            response = generate_credit_report_csv_response(queryset)

            return response
        return super().get(request, *args, **kwargs)
