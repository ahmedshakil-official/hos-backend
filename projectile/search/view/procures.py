from django.conf import settings

from rest_framework import generics

from elasticsearch_dsl import Q

from core.permissions import (
    CheckAnyPermission,
    StaffIsAdmin,
    StaffIsDistributionT1,
    StaffIsProcurementOfficer,
    StaffIsProcurementBuyerWithSupplier,
)
from procurement.serializers.procure import ProcureModelSerializer
from ..document.procures import ProcureDocument


class ProcureSearchView(generics.ListAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsDistributionT1,
        StaffIsProcurementOfficer,
        StaffIsProcurementBuyerWithSupplier,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProcureModelSerializer.List

    def get_queryset(self):
        query_value = self.request.query_params.get("keyword", None)
        page_size = self.request.query_params.get(
            "page_size", settings.ES_PAGINATION_SIZE
        )

        search = ProcureDocument.search()

        if query_value and query_value.isdigit():
            search = search.query(
                "bool",
                should=[
                    {"term": {"id": query_value}},
                    {"term": {"requisition.pk": query_value}},
                ],
            )

        elif query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=[
                    "employee.first_name",
                    "employee.code",
                    "supplier.first_name",
                    "supplier.code",
                    "invoices",
                ],
            )

        response = search[: int(page_size)].execute()
        return response
