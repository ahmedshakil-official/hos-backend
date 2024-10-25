from django.conf import settings
from rest_framework import generics
from rest_framework import status
from rest_framework.exceptions import APIException

from elasticsearch_dsl import Q

from common.enums import Status
from common.utils import string_to_bool
from common.helpers import (
    custom_elastic_rebuild,
)

from core.permissions import (
    CheckAnyPermission,
    StaffIsAccountant,
    StaffIsAdmin,
    StaffIsLaboratoryInCharge,
    StaffIsProcurementOfficer,
    StaffIsReceptionist,
    StaffIsSalesman,
    StaffIsSalesReturn,
    StaffIsTelemarketer,
    StaffIsDeliveryHub,
    StaffIsSalesCoordinator,
    StaffIsDistributionT1,
    StaffIsDistributionT2,
    StaffIsDistributionT3,
    StaffIsFrontDeskProductReturn,
    StaffIsSalesManager,
)

from search.document.ecommerce import (
    OrderInvoiceGroupDocument,
)

from search.utils import search_by_multiple_aliases

from ecommerce.serializers.order_invoice_group import OrderInvoiceGroupModelSerializer


class OrderInvoiceGroupSearchView(generics.ListAPIView):
    available_permission_classes = (
        StaffIsAccountant,
        StaffIsAdmin,
        StaffIsSalesman,
        StaffIsSalesReturn,
        StaffIsTelemarketer,
        StaffIsDeliveryHub,
        StaffIsSalesCoordinator,
        StaffIsDistributionT1,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsFrontDeskProductReturn,
        StaffIsSalesManager,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = OrderInvoiceGroupModelSerializer.Search

    def get_queryset(self):
        order_by_organization = self.request.query_params.get("organization", None)
        query_value = self.request.query_params.get('keyword', None)
        rating = self.request.query_params.get('rating', None)
        is_invoice_group_id = string_to_bool(
            self.request.query_params.get('is_invoice_group_id', None))
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = OrderInvoiceGroupDocument.search()
        # if search by invoice group id then check is it valid id
        if is_invoice_group_id:
            try:
                int(query_value)
            except ValueError:
                detail= f"{query_value} is invalid. Please provide valid invoice group id."
                raise APIException(detail=detail, code=status.HTTP_400_BAD_REQUEST)

        # Filter for specific organization
        if order_by_organization:
            search = search.query(
                Q('match', order_by_organization__alias=order_by_organization)
            )

        # Filter for rating
        if rating:
            search = search.query(
                Q('match', customer_rating=rating)
            )

        search, aliases = search_by_multiple_aliases(self.request, search)

        if query_value and query_value.isdigit() and not is_invoice_group_id:
            search = search.query(
                "multi_match",
                query=query_value,
                type="cross_fields",
                fields=['id', 'orders.pk']
            )
        elif query_value and query_value.isdigit() and is_invoice_group_id:
            search = search.query(
                "multi_match",
                query=query_value,
                type="cross_fields",
                fields=['id', ]
            )
            # search = search.query(
            #     Q('terms', id=[query_value])
            # )
        elif query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=[
                    'alias',
                    'order_by_organization.name',
                    'order_by_organization.primary_mobile',
                ]
            )
        search = search.query(
            Q('match', organization__pk=self.request.user.organization_id) &
            Q('exists', field='orders') &
            Q('match', status=Status.ACTIVE)
        ).sort('-date')
        response = search[:int(page_size)].execute()
        # Populate index for missing data

        if is_invoice_group_id and not response.hits:
            try:
                custom_elastic_rebuild(
                    'ecommerce.models.OrderInvoiceGroup',
                    {'pk': query_value}
                )
            except:
                pass

        if aliases:
            self.pagination_class.page_size = search.count()

        return response
