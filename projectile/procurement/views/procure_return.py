"""Views for Procure return related models."""

from operator import attrgetter
from itertools import chain

from django.db.models import Sum, F, Subquery, OuterRef, IntegerField, Prefetch
from django.db.models.functions import Coalesce

from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from common.enums import Status
from core.views.common_view import (
    ListCreateAPICustomView,
    ListAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
)

from core.permissions import (
    CheckAnyPermission,
    IsSuperUser,
    StaffIsAdmin,
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator,
    StaffIsDistributionT1,
)

from common.enums import Status

from procurement.utils import calculate_total_settled_amount
from procurement.filters import ProcureReturnListFilter
from procurement.serializers.procure_return import (
    ProcureReturnModelSerializer,
    ProcurePurchaseListProductContractorWiseSerializer,
)
from procurement.serializers.procure_return_settlement import (
    ReturnSettlementModelSerializer,
)
from procurement.filters import ProcureItemPurchaseListFilter
from ..enums import ProcureStatus
from ..models import ProcureItem, ProcureReturn, ReturnSettlement


class ProcurePurchaseListProductContractorWise(ListAPIView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProcurePurchaseListProductContractorWiseSerializer
    filterset_class = ProcureItemPurchaseListFilter
    pagination_class = None

    def get_queryset(self, related_fields=None, only_fields=None):
        queryset = (
            ProcureItem()
            .get_all_actives().filter(
                procure__current_status__in=[
                    ProcureStatus.DELIVERED,
                    ProcureStatus.PAID,
                    ProcureStatus.COMPLETED
                ])
            .values("stock_id")
            .annotate(
                total_quantity=Sum("quantity"),
                total_return_quantity=Coalesce(
                    Subquery(
                        ProcureReturn.objects.filter(
                            # avoided get_all_actives to fix quantity sum mismatch
                            status=Status.ACTIVE,
                            procure=OuterRef("procure"),
                        )
                        .values("procure")
                        .annotate(total_return_quantity=Sum("quantity"))
                        .values("total_return_quantity")[:1],
                        output_field=IntegerField(),
                    ),
                    0,
                ),
                rate=F("rate"),
                product_name=F("product_name"),
                company_name=F("company_name"),
                procure_id=F("procure__id"),
                date=F("date"),
            )
            .distinct()
            .order_by("stock__id")
        )
        return queryset


class ProcureReturnList(ListCreateAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProcureReturnModelSerializer.List
    filterset_class = ProcureReturnListFilter

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProcureReturnModelSerializer.List
        return ProcureReturnModelSerializer.Post

    def get_queryset(self, related_fields=None, only_fields=None):
        related_fields = ["procure", "employee", "contractor"]
        queryset = super().get_queryset(related_fields, only_fields).order_by("-pk")
        queryset = queryset.prefetch_related("procure_return_settlements",)

        return queryset


class ProcureReturnDetail(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProcureReturnModelSerializer.List
    lookup_field = "alias"

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProcureReturnModelSerializer.List
        return ProcureReturnModelSerializer.Detail

    def get_queryset(self):
        alias = self.kwargs.get("alias")
        queryset = (
            super()
            .get_queryset()
            .filter(alias=alias)
            .select_related("procure", "employee", "contractor")
        )
        return queryset

    def perform_destroy(self, instance):
        instance.status = Status.INACTIVE
        instance.update_by_id = self.request.user.id
        instance.save(
            update_fields=["status", "updated_by_id"],
        )
        return_settlement = instance.procure_return_settlements.filter(
            status=Status.ACTIVE
        )
        return_settlement.update(status=Status.INACTIVE)


class ReturnSettlementDetail(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    lookup_field = "alias"
    serializer_class = ReturnSettlementModelSerializer.List

    def get_queryset(self):
        alias = self.kwargs.get("alias")
        queryset = (
            super()
            .get_queryset()
            .filter(alias=alias)
            .select_related("procure_return", "employee")
        )

        return queryset

    def perform_destroy(self, instance):
        instance.status = Status.INACTIVE
        instance.save(update_fields=["status"])
        calculate_total_settled_amount(instance.procure_return)
        return super().perform_destroy(instance)


class ReturnSettlementList(ListCreateAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ReturnSettlementModelSerializer.List
        return ReturnSettlementModelSerializer.Post

    def get_queryset(self, related_fields=None, only_fields=None):
        queryset = ReturnSettlement().get_all_actives().select_related(
            "procure_return",
            "employee"
        )

        return queryset


class ProcureReturnSettlementLog(ListAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProcureReturnModelSerializer.List

    def get_queryset(self):
        alias = self.kwargs.get("alias", None)
        queryset = (
            ProcureReturn.objects.select_related("contractor", "procure", "employee")
            .filter(
                procure__alias=alias,
            )
        )

        return queryset

    def get(self, request, *args, **kwargs):
        procure_returns = self.get_queryset()
        return_settlements = (
            ReturnSettlement
            .objects
            .filter(procure_return__in=procure_returns)
            .select_related("employee", "procure_return")
        ).annotate(
            product_name=F("procure_return__product_name"),
            quantity=F("procure_return__quantity")
        )
        # Combine and return and settlements data
        returns_and_settlements = sorted(
            chain(procure_returns, return_settlements),
            key=attrgetter("created_at"),
            reverse=True,
        )
        results = []
        for item in returns_and_settlements:
            if isinstance(item, ProcureReturn):
                serialized_data = ProcureReturnModelSerializer.List(item).data
                serialized_data["is_procure_return"] = True
            else:
                serialized_data = ReturnSettlementModelSerializer.List(item).data
                serialized_data["is_return_settlement"] = True
            # Append the result in the results dictionary
            results.append(serialized_data)

        return Response({"results": results}, status=status.HTTP_200_OK)
