from time import sleep

from django.db.models.functions import Coalesce, Concat
from django.db.models import (
    F,
    Value,
    Case,
    When,
    Sum,
    FloatField,
    Q,
    Count,
    BooleanField,
)

from rest_framework.exceptions import ValidationError as drf_ValidationError
from rest_framework import serializers
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response


from common.utils import DistinctSum
from common.enums import Status
from core.serializers import PersonOrganizationEmployeeSearchSerializer
from core.views.common_view import(
    ListCreateAPICustomView,
    CreateAPICustomView,
    ListAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
)
from core.mixins import MultipleFieldLookupMixin
from core.permissions import (
    CheckAnyPermission,
    IsSuperUser,
    StaffIsAdmin,
    AnyLoggedInUser,
    StaffIsDeliveryMan,
    StaffIsMarketer,
    StaffIsDeliveryHub,
    StaffIsSalesCoordinator,
    StaffIsSalesManager,
    StaffIsDistributionT1,
    StaffIsDistributionT2,
    StaffIsDistributionT3,
)
from core.custom_serializer.organization import (
    OrganizationModelSerializer,
)
from pharmacy.models import StockIOLog
from pharmacy.enums import OrderTrackingStatus
from ecommerce.serializers.invoice_group_delivery_sheet import InvoiceGroupDeliverySheetModelSerializer
from ..filters import InvoiceGroupDeliverySheetListFilter, assigned_unassigned_filter
from ..models import DeliverySheetInvoiceGroup, OrderInvoiceGroup, InvoiceGroupDeliverySheet
from ..enums import ShortReturnLogType, AssignedUnassignedState, TopSheetType
from ..serializers.common import (
    DeliverySheetShortReturnListProductWiseSerializer,
    DeliverySheetStockShortReturnListInvoiceGroupWiseSerializer,
)
from core.models import PersonOrganization, Organization
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status

from ..models import DeliverySheetItem, TopSheetSubTopSheet
from ..serializers import delivery_sheet_item


class InvoiceGroupDeliverySheetListCreate(ListCreateAPICustomView):

    available_permission_classes = ()
    filterset_class = InvoiceGroupDeliverySheetListFilter

    def get_permissions(self):
        if self.request.method == "GET":
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsMarketer,
                StaffIsDeliveryHub,
                StaffIsSalesCoordinator,
                StaffIsSalesManager,
                StaffIsDistributionT3,
                StaffIsDistributionT2,
            )
        else:
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsDeliveryHub,
                StaffIsSalesManager,
                StaffIsSalesCoordinator,
                StaffIsDistributionT3,
                StaffIsDistributionT2,
            )
        return (CheckAnyPermission(),)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return InvoiceGroupDeliverySheetModelSerializer.List
        return InvoiceGroupDeliverySheetModelSerializer.Post

    def get_queryset(self, related_fields=None, only_fields=None):
        related_fields = [
            "responsible_employee",
            "coordinator",
            "generated_by",
        ]
        return super().get_queryset(related_fields, only_fields).order_by("-pk")


class InvoiceGroupDeliverySheetDetails(MultipleFieldLookupMixin, RetrieveUpdateDestroyAPICustomView):

    def get_serializer_class(self):
        if self.request.method == "GET":
            return InvoiceGroupDeliverySheetModelSerializer.Details
        return InvoiceGroupDeliverySheetModelSerializer.Details

    available_permission_classes = ()
    lookup_fields = ["alias", "pk", "name"]

    def get_permissions(self):
        if self.request.method == "GET":
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsMarketer,
                StaffIsDeliveryHub,
                StaffIsDistributionT3,
                StaffIsSalesManager,
                StaffIsSalesCoordinator,
            )
        else:
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsDeliveryHub,
                StaffIsDistributionT3,
                StaffIsSalesManager,
                StaffIsSalesCoordinator,
            )
        return (CheckAnyPermission(),)

    def get_queryset(self):
        return super().get_queryset().select_related(
            "coordinator",
        ).prefetch_related(
            "delivery_sheet_items__order_by_organization",
            "delivery_sheet_items__delivery_sheet_invoice_groups",
            "delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group",
            "sub_top_sheet_delivery_sheet_items__order_by_organization",
            "sub_top_sheet_delivery_sheet_items__delivery_sheet_invoice_groups",
            "sub_top_sheet_delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group",
        )

    def perform_destroy(self, instance):
        if instance.type == TopSheetType.SUB_TOP_SHEET:
            # find all DeliverySheetItem for the sub_sheet and remove sub_sheet reference
            delivery_sheet_items = DeliverySheetItem().get_all_actives().filter(
                invoice_group_delivery_sub_sheet__id=instance.id
            )
            delivery_sheet_items.update(invoice_group_delivery_sub_sheet=None)
        return super().perform_destroy(instance)


class DeliverySheetShortReturnListProductWise(ListAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = DeliverySheetShortReturnListProductWiseSerializer

    def get(self, request, delivery_sheet_id):

        if not delivery_sheet_id:
            return Response({}, status=status.HTTP_200_OK)
        invoices = DeliverySheetInvoiceGroup.objects.filter(
            delivery_sheet_item__invoice_group_delivery_sheet__id=delivery_sheet_id
        ).values_list('invoice_group_id', flat=True)

        invoice_amount_summary = OrderInvoiceGroup.objects.filter(
            pk__in=invoices
        ).aggregate(
            total_invoice_amount=Coalesce(
                DistinctSum(
                    F('sub_total') + F('round_discount') - F('discount') - F('additional_discount'),
                    output_field=FloatField()
                ),
                0.00
            ),
            total_short=Coalesce(
                Sum(
                    Case(
                        When(
                            ~Q(status=Status.INACTIVE) &
                            ~Q(invoice_groups__status=Status.INACTIVE) &
                            Q(invoice_groups__type=ShortReturnLogType.SHORT),
                            then=F('invoice_groups__short_return_amount') + F('invoice_groups__round_discount')
                        ),
                        output_field=FloatField()
                    )
                ),
                0.00
            ),
            total_return=Coalesce(
                Sum(
                    Case(
                        When(
                            ~Q(status=Status.INACTIVE) &
                            ~Q(invoice_groups__status=Status.INACTIVE) &
                            Q(invoice_groups__type=ShortReturnLogType.RETURN),
                            then=F('invoice_groups__short_return_amount') + F('invoice_groups__round_discount')
                        ),
                        output_field=FloatField()
                    )
                ),
                0.00
            ),
        )

        io_items = StockIOLog.objects.filter(
            purchase__invoice_group__in=invoices,
            status=Status.DISTRIBUTOR_ORDER,
        ).order_by().values(
            'stock_id',
            'stock__alias',
            'stock__product__name',
            'stock__product__strength',
            'stock__product__form__name',
        ).annotate(
            total_short_quantity=Coalesce(Sum(
                Case(
                    When(
                        ~Q(stock_io_short_return__status=Status.INACTIVE) &
                        Q(stock_io_short_return__type=ShortReturnLogType.SHORT),
                        then=F('stock_io_short_return__quantity'),
                    ),
                    output_field=FloatField()
                ),
            ), 0.00),
            total_return_quantity=Coalesce(Sum(
                Case(
                    When(
                        ~Q(stock_io_short_return__status=Status.INACTIVE) &
                        Q(stock_io_short_return__type=ShortReturnLogType.RETURN),
                        then=F('stock_io_short_return__quantity')
                    ),
                    output_field=FloatField()
                ),
            ), 0.00),
            total_order_quantity=Coalesce(DistinctSum('quantity'), 0.00),
            # product_name=Concat(
            #     'stock__product__form__name',
            #     Value(''),
            #     'stock__product__name',
            #     Value(''),
            #     'stock__product__strength'
            # )
        )
        response = {
            "items": DeliverySheetShortReturnListProductWiseSerializer(io_items, many=True).data,
            "summary": invoice_amount_summary
        }
        return Response(response, status=status.HTTP_200_OK)

class DeliverySheetStockShortReturnListInvoiceGroupWise(ListAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = DeliverySheetStockShortReturnListInvoiceGroupWiseSerializer
    pagination_class = None

    def get_queryset(self):
        delivery_sheet_id = self.kwargs.get('delivery_sheet_id', '')
        stock_alias = self.kwargs.get('stock_alias', '')
        invoices = DeliverySheetInvoiceGroup.objects.filter(
            delivery_sheet_item__invoice_group_delivery_sheet__id=delivery_sheet_id
        ).values_list('invoice_group_id', flat=True)

        queryset = StockIOLog.objects.filter(
            purchase__invoice_group__in=invoices,
            status=Status.DISTRIBUTOR_ORDER,
            stock__alias=stock_alias,
        ).order_by().values(
            'purchase__invoice_group_id',
        ).annotate(
            total_short_quantity=Coalesce(Sum(
                Case(
                    When(
                        ~Q(stock_io_short_return__status=Status.INACTIVE) &
                        Q(stock_io_short_return__type=ShortReturnLogType.SHORT),
                        then=F('stock_io_short_return__quantity'),
                    ),
                    output_field=FloatField()
                ),
            ), 0.00),
            total_return_quantity=Coalesce(Sum(
                Case(
                    When(
                        ~Q(stock_io_short_return__status=Status.INACTIVE) &
                        Q(stock_io_short_return__type=ShortReturnLogType.RETURN),
                        then=F('stock_io_short_return__quantity')
                    ),
                    output_field=FloatField()
                ),
            ), 0.00),
            total_order_quantity=Coalesce(DistinctSum('quantity'), 0.00),
        )
        return queryset


class DeliverySheetDataSpecificDayWise(APIView):
    """
        API endpoint to retrieve delivery sheet data for a specific day based on the responsible employee's alias.

        This view fetches the delivery sheet number and name for a given date corresponding to the specified responsible
        employee's alias.
        Additionally, it retrieves manager data for the same responsible employee.

        Parameters:
        - `responsible_employee_alias` (str): Alias of the responsible employee.
        - `date` (str): Date for which the delivery sheet data is required.

        Permission:
        - Any logged-in user can access this view.
    """

    permission_classes = (AnyLoggedInUser,)

    def get(self, request, responsible_employee_alias, date):

        date = str(date)
        try:
            person_organization = PersonOrganization.objects.only(
                "id",
                "code",
            ).get(alias=responsible_employee_alias)

            delivery_sheet_number = person_organization.get_delivery_sheet_number(date)
            delivery_sheet_name = person_organization.get_delivery_sheet_name(date)
            coordinator = person_organization.manager

            coordinator_serializer = PersonOrganizationEmployeeSearchSerializer(coordinator).data if coordinator else None

            delivery_data ={
                "delivery_sheet_number": delivery_sheet_number,
                "delivery_sheet_name": delivery_sheet_name,
                "coordinator": coordinator_serializer
            }
            return Response(delivery_data, status=status.HTTP_200_OK)

        except Exception as exception:
            exception_str = exception.args[0] if exception.args else str(exception)
            content = {f"error: {exception_str}"}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class InvoiceGroupDeliverySheetInfo(RetrieveAPIView):
    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = InvoiceGroupDeliverySheetModelSerializer.Info
    queryset = InvoiceGroupDeliverySheet.objects.filter()
    lookup_field = 'pk'


class FixInvoiceGroupDeliverySheetMismatch(APIView):

    def post(self, request, *args, **kwargs):
        from ecommerce.utils import update_short_return_for_invoice_group_related_models_through_top_sheet_id

        alias = self.kwargs.get('alias', None)
        if alias:
            update_short_return_for_invoice_group_related_models_through_top_sheet_id(alias)
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class DeliverySheetOrganizationPrimaryResponsiblePerson(MultipleFieldLookupMixin, APIView):
    serializer_class = OrganizationModelSerializer.LiteWithResponsiblePerson

    lookup_fields = ["alias", "id"]

    def get_organization_pk_list(self, request, **kwargs):
        top_sheet_id = kwargs.get("id", None)
        top_sheet_alias = kwargs.get("alias", None)

        if top_sheet_id:
            items = DeliverySheetItem.objects.filter(
                invoice_group_delivery_sheet__id=top_sheet_id,
                status=Status.ACTIVE,
            ).values_list("order_by_organization_id", flat=True)
            return items

        if top_sheet_alias:
            items = DeliverySheetItem.objects.filter(
                invoice_group_delivery_sheet__alias=top_sheet_alias,
                status=Status.ACTIVE,
            ).values_list("order_by_organization_id", flat=True)
            return items
        return []

    def get(self, request, **kwargs):

        organizations = Organization.objects.filter(
            id__in=self.get_organization_pk_list(request, **kwargs)
        ).select_related(
            "primary_responsible_person",
        ).only(
            "id",
            "alias",
            "name",
            "status",
            "primary_mobile",
            "address",
            "delivery_thana",
            "active_issue_count",
            "delivery_sub_area",
            "geo_location",
            "primary_responsible_person__id",
            "primary_responsible_person__alias",
            "primary_responsible_person__phone",
            "primary_responsible_person__first_name",
            "primary_responsible_person__last_name",
            "primary_responsible_person__code",
        )
        serializer = self.serializer_class(organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AssignedUnAssignedDelivery(ListAPICustomView):
    """
    Args:
        ListAPICustomView (rest_framework view class):
        finds deliveries those aren't assigned to a top sub sheet or
        assigned to a top sub sheet.

    Returns:
        dict(json): contains unassigned or assigned deliveries for a top sheet.
        value changed by query keyword
    """
    serializer_class = (
        delivery_sheet_item.DeliverySheetItemModelSerializer.DeliverySheetItemSerializerWithPorterAndInvoice
    )

    def get_serializer_class(self):
        if self.request.query_params.get("state", None) == AssignedUnassignedState.Unassigned:
            return super().get_serializer_class()
        else:
            return delivery_sheet_item.DeliverySheetItemModelSerializer.DeliverySheetItemSerializerWithPorterAndInvoiceAssignee


    def get_queryset(self, related_fields=None, only_fields=None):
        invoice_group_delivery_sheet_alias = self.kwargs.get("alias", None)
        try:
            state = self.request.query_params.get("state", None)
            query_params = self.request.query_params.copy()
            query_params.pop("state")
        except KeyError:
            raise drf_ValidationError(
            {
                "detail": "This endpoint is only for filtering. add `?state=unassigned or assigned` after deliveries/",
                "example": "http://127.0.0.1:8000/api/v1/ecommerce/invoice-group/delivery-sheet/81d120cb-2ba2-42b1-a5ef-2537d6cf3ee8/deliveries/?state=unassigned",
            }
        )

        # check if sub sheet is created by the top sheet which alias has given
        sub_top_sheet = (
            TopSheetSubTopSheet()
            .get_all_actives()
            .filter(top_sheet__alias=invoice_group_delivery_sheet_alias)
        )
        if sub_top_sheet.exists():
            # if true means some or all deliveries are assigned

            # get all the top sub sheet ids aka assigned deliveries invoice ids
            sub_top_sheet_ids = sub_top_sheet.values_list(
                "sub_top_sheet__id", flat=True
            )
            if state and state.lower() == AssignedUnassignedState.Unassigned:
                deliveries = (
                    DeliverySheetItem()
                    .get_all_actives()
                    .filter(
                        invoice_group_delivery_sheet__alias=invoice_group_delivery_sheet_alias,
                        invoice_group_delivery_sub_sheet__isnull=True
                    )
                    .exclude(invoice_group_delivery_sub_sheet__id__in=sub_top_sheet_ids)
                    .select_related(
                        "order_by_organization",
                        'order_by_organization__primary_responsible_person',
                        "invoice_group_delivery_sheet__responsible_employee",
                    )
                ).annotate(is_assigned=Value(False, output_field=BooleanField()))

                filter_conditions = assigned_unassigned_filter(query_params)

                if filter_conditions:
                    deliveries = deliveries.filter(Q(*filter_conditions, _connector=Q.OR))

            if state and state.lower() == AssignedUnassignedState.Assigned:
                deliveries = (
                    DeliverySheetItem.objects.filter(
                        invoice_group_delivery_sheet__alias=invoice_group_delivery_sheet_alias,
                    )
                    .exclude(invoice_group_delivery_sub_sheet__isnull=True)
                    .select_related(
                        "order_by_organization",
                        'order_by_organization__primary_responsible_person',
                        "invoice_group_delivery_sheet__responsible_employee",
                    )
                ).annotate(is_assigned=Value(True, output_field=BooleanField()))
                filter_conditions = assigned_unassigned_filter(query_params)

                if filter_conditions:
                    deliveries = deliveries.filter(Q(*filter_conditions, _connector=Q.OR))

            return deliveries

        else:
            # means none of the deliveries are assigned thus return all delivery list

            # if all deliveries are unassigned and state==assigned return none
            if state and state.lower() == AssignedUnassignedState.Assigned:
                return DeliverySheetItem.objects.none()

            unassigned_deliveries = (
                DeliverySheetItem()
                .get_all_actives()
                .filter(
                    invoice_group_delivery_sheet__alias=invoice_group_delivery_sheet_alias
                )
            ).select_related(
                'order_by_organization',
                'order_by_organization__primary_responsible_person',
                'invoice_group_delivery_sheet__responsible_employee',
            ).annotate(is_assigned=Value(False, output_field=BooleanField()))

            filter_conditions = assigned_unassigned_filter(query_params)
            if filter_conditions:
                unassigned_deliveries = unassigned_deliveries.filter(Q(*filter_conditions, _connector=Q.OR))

            return unassigned_deliveries


    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        delivery_item_ids = queryset.values_list("id", flat=True)

        # Calculate the completed deliveries for each invoice group delivery sheet
        completed_deliveries_count = OrderInvoiceGroup().get_all_actives().filter(
            delivery_sheet_invoice_groups__delivery_sheet_item__id__in=delivery_item_ids
        ).exclude(
            current_order_status__in=[
                OrderTrackingStatus.PENDING,
                OrderTrackingStatus.ACCEPTED,
                OrderTrackingStatus.READY_TO_DELIVER,
                OrderTrackingStatus.ON_THE_WAY,
                OrderTrackingStatus.REJECTED,
                OrderTrackingStatus.CANCELLED,
                OrderTrackingStatus.IN_QUEUE,
            ]
        ).select_related(
            "delivery_sheet_invoice_groups__delivery_sheet_item"
            ).count()

        # Count the number of items in the querysets
        total_deliveries = queryset.count()

        status = 'Pending'
        if total_deliveries == completed_deliveries_count:
            status = 'Completed'
        elif completed_deliveries_count > 0:
            status = 'In Progress'

        # Get the paginated queryset
        paginated_queryset = self.paginate_queryset(queryset)

        # Serialize the paginated queryset
        serializer = self.get_serializer(paginated_queryset, many=True)

        # Modify the serialized data to include the 'status' field
        modified_data = []
        for item in serializer.data:
            item['status'] = status
            modified_data.append(item)

        # Return the paginated modified data in the response
        return self.get_paginated_response(modified_data)


class CompletedDeliveriesCount(APIView):
    available_permission_classes = (
        AnyLoggedInUser,
    )
    permission_classes = (CheckAnyPermission, )

    def get(self, request, *args, **kwargs):
         # Retrieve the list of invoice_group_delivery_sheet_id values from the query parameters
        invoice_group_delivery_sheet = request.GET.get("top_sheet_ids")

        if not invoice_group_delivery_sheet:
            return Response(
            {"message": "You must provide top sheet ids to get completed deliveries count"},
            status=status.HTTP_400_BAD_REQUEST,
        )
        invoice_group_delivery_sheet_ids = invoice_group_delivery_sheet.split(",")
        completed_counts = OrderInvoiceGroup().get_all_actives().filter(
            delivery_sheet_invoice_groups__delivery_sheet_item__invoice_group_delivery_sheet_id__in=invoice_group_delivery_sheet_ids,
        ).exclude(
            current_order_status__in=[
                OrderTrackingStatus.PENDING,
                OrderTrackingStatus.ACCEPTED,
                OrderTrackingStatus.READY_TO_DELIVER,
                OrderTrackingStatus.ON_THE_WAY,
                OrderTrackingStatus.REJECTED,
                OrderTrackingStatus.CANCELLED,
                OrderTrackingStatus.IN_QUEUE,
            ]
        ).values('delivery_sheet_invoice_groups__delivery_sheet_item__invoice_group_delivery_sheet_id').annotate(
            completed_deliveries=Count('id')
        )

        completed_counts_dict = {}
        for entry in completed_counts:
            invoice_group_delivery_sheet_id = entry['delivery_sheet_invoice_groups__delivery_sheet_item__invoice_group_delivery_sheet_id']
            completed_deliveries = entry['completed_deliveries']
            completed_counts_dict[invoice_group_delivery_sheet_id] = completed_counts_dict.get(invoice_group_delivery_sheet_id, 0) + completed_deliveries

        # Set the count to 0 for invoice_group_delivery_sheet_ids with no Completed instance
        for invoice_group_delivery_sheet_id in invoice_group_delivery_sheet_ids:
            if int(invoice_group_delivery_sheet_id) not in completed_counts_dict:
                completed_counts_dict[int(invoice_group_delivery_sheet_id)] = 0

        return Response(
            {"completed_deliveries": completed_counts_dict},
            status=status.HTTP_200_OK
        )
