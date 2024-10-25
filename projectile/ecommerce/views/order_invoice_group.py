import decimal
import re
from datetime import datetime, timedelta, time
import decimal
from uuid import UUID

from django.utils import timezone
from rest_framework.exceptions import ValidationError
from validator_collection import checkers
from django.db import transaction
from django.core.cache import cache
from django.db import transaction
from django.db.utils import IntegrityError
from django.db.models import (
    Case,
    F,
    Q,
    Sum,
    When,
    Prefetch,
    FloatField,
    Count,
    Func,
    IntegerField,
    Value,
    Subquery,
    CharField,
    DateField,
)
from django.db.models.functions import Coalesce, Cast, Concat, JSONObject
from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg

from rest_framework.generics import (
    RetrieveUpdateAPIView,
    UpdateAPIView,
    ListAPIView
)
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.views import APIView

from common.helpers import (
    custom_elastic_rebuild,
    to_boolean,
    send_log_alert_to_slack_or_mattermost,
    get_date_range_from_period,
)
from common.utils import (
    DistinctSum,
    ArrayLength, Round,
)
from common.enums import Status
from common.cache_helpers import delete_qs_count_cache
from common.pagination import CachedCountPageNumberPagination
from core.tasks import update_organization_responsible_employee_from_organization_list

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
    StaffIsMarketer,
    StaffIsProcurementOfficer,
    StaffIsNurse,
    StaffIsReceptionist,
    StaffIsTelemarketer,
    StaffIsDeliveryHub,
    StaffIsSalesCoordinator,
    StaffIsFrontDeskProductReturn,
    StaffIsSalesManager,
    StaffIsDistributionT1,
    StaffIsDistributionT2,
    StaffIsDistributionT3,
    StaffIsAccountant,
)
from core.enums import OrganizationType
from ecommerce.utils import (
    update_invoice_group_additional_discount_amount,
    get_dynamic_discount_message
)

from pharmacy.models import Purchase, StockIOLog, OrderTracking
from pharmacy.custom_serializer.order_tracking import (
    OrderTrackingModelSerializer,
)
from pharmacy.enums import OrderTrackingStatus, PurchaseType, DistributorOrderType
from search.utils import update_order_invoice_group_es_doc

from ecommerce.serializers.order_invoice_group import (
    OrderInvoiceGroupModelSerializer,
    InvoiceGroupProductSumSerializer,
    InvoiceGroupProductQuantityInvoiceCountSerializer,
)
from ecommerce.serializers.common import ResponsibleEmployeeWiseInvoiceGroupDeliverySheetSerializer
from ecommerce.models import OrderInvoiceGroup, ShortReturnLog, ShortReturnItem
from ecommerce.filters import OrderInvoiceGroupListFilter
from ecommerce.enums import ShortReturnLogType
from ecommerce.tasks import (
    update_es_index_for_related_invoices,
    send_invoice_status_change_log_to_mm,
)
from pharmacy.utils import get_tentative_delivery_date, get_discount_for_cart_and_order_items, get_minimum_order_amount
from pharmacy.custom_serializer.order_tracking import OrderTrackingModelSerializer


class OrderInvoiceGroupListCreate(ListCreateAPICustomView):
    available_permission_classes = ()

    def get_permissions(self):
        if self.request.method == "GET":
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsMarketer,
                StaffIsDeliveryHub,
                StaffIsSalesCoordinator,
                StaffIsFrontDeskProductReturn,
                StaffIsSalesManager,
                StaffIsDistributionT2,
                StaffIsDistributionT3,
                StaffIsAccountant,
                StaffIsTelemarketer,
            )
        else:
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsMarketer,
                StaffIsSalesCoordinator,
                StaffIsDistributionT2,
                StaffIsDistributionT3,
            )
        return (CheckAnyPermission(),)

    filterset_class = OrderInvoiceGroupListFilter
    pagination_class = CachedCountPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return OrderInvoiceGroupModelSerializer.List
        return OrderInvoiceGroupModelSerializer.Post

    def get_queryset(self):
        order_by_area_subarea = to_boolean(self.request.query_params.get('order_by_area_subarea', False))
        order_by_responsible_person_area_subarea = to_boolean(self.request.query_params.get('order_by_responsible_person_area_subarea', False))
        order_filters = {
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER,
            "distributor__id": self.request.user.organization_id
        }
        orders = Purchase.objects.filter(
            **order_filters
        ).only(
            'id',
            'invoice_group_id',
        )
        queryset = OrderInvoiceGroup.objects.filter(
            status=Status.ACTIVE,
            organization__id=self.request.user.organization_id,
            orders__isnull=False
        ).only(
            'id',
            'alias',
            'round_discount',
            'discount',
            'sub_total',
            'delivery_date',
            'date',
            'current_order_status',
            'additional_discount',
            'additional_discount_rate',
            'total_return',
            'total_short',
            'additional_cost',
            'customer_rating',
            'customer_comment',
            'order_by_organization__id',
            'order_by_organization__alias',
            'order_by_organization__name',
            'order_by_organization__primary_mobile',
            'order_by_organization__status',
            'order_by_organization__delivery_thana',
            'order_by_organization__delivery_sub_area',
            'order_by_organization__address',
            'order_by_organization__active_issue_count',
            'order_by_organization__entry_by__id',
            'order_by_organization__entry_by__alias',
            'order_by_organization__entry_by__first_name',
            'order_by_organization__entry_by__last_name',
            'order_by_organization__entry_by__phone',
            'order_by_organization__entry_by__code',
            'responsible_employee__id',
            'responsible_employee__alias',
            'responsible_employee__first_name',
            'responsible_employee__last_name',
            'responsible_employee__phone',
            'responsible_employee__code',
            'responsible_employee__person_group',
            'responsible_employee__company_name',
        ).select_related(
            'responsible_employee',
            'order_by_organization',
            'order_by_organization__entry_by',
        ).prefetch_related(
            Prefetch(
                'orders',
                queryset=orders
            )
        ).distinct()

        if not order_by_area_subarea and not order_by_responsible_person_area_subarea:
            return queryset.order_by('-pk')

        if order_by_area_subarea:
            return queryset.order_by(
                'order_by_organization__delivery_thana',
                'order_by_organization__delivery_sub_area',
                'order_by_organization__primary_responsible_person',
                '-pk',
            )
        if order_by_responsible_person_area_subarea:
            return queryset.order_by(
                'order_by_organization__primary_responsible_person',
                'order_by_organization__delivery_thana',
                'order_by_organization__delivery_sub_area',
                '-pk',
            )

    def post(self, request):
        try:
            serializer = OrderInvoiceGroupModelSerializer.Post(
                data=request.data,
                context={'request': request}
            )
            if serializer.is_valid(raise_exception=True):
                serializer = serializer.save()
                # Delete qs count cache
                delete_qs_count_cache(OrderInvoiceGroup)
                return Response({"message": "Success"}, status=status.HTTP_201_CREATED)
            return Response({"message": "Failed"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as exception:
            exception_str = exception.args[0] if exception.args else str(exception)
            content = {'error': '{}'.format(exception_str)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class OrderInvoiceGroupDetails(MultipleFieldLookupMixin, RetrieveUpdateDestroyAPICustomView):

    available_permission_classes = (
        StaffIsFrontDeskProductReturn,
        StaffIsDeliveryHub
    )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return OrderInvoiceGroupModelSerializer.Details
        return OrderInvoiceGroupModelSerializer.Update


    def get_permissions(self):
        is_distributor = self.request.user.profile_details.organization.type == OrganizationType.DISTRIBUTOR
        request_data = self.request.data if self.request.data else {}
        is_print_count_update = self.request.method == 'PATCH' and len(request_data.keys()) == 1 and 'print_count' in request_data.keys()
        if self.request.method == 'GET' or (self.request.method == 'PATCH' and is_distributor):
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsMarketer,
                StaffIsTelemarketer,
                StaffIsDeliveryHub,
                StaffIsSalesCoordinator,
                StaffIsFrontDeskProductReturn,
                StaffIsSalesManager,
                StaffIsDistributionT2,
                StaffIsDistributionT3,
                StaffIsAccountant,
                StaffIsTelemarketer,
            )
        elif is_print_count_update:
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsNurse,
                StaffIsProcurementOfficer,
                StaffIsReceptionist,
                IsSuperUser,
                StaffIsReceptionist,
                StaffIsMarketer,
                StaffIsFrontDeskProductReturn,
                StaffIsSalesManager,
                StaffIsDistributionT2,
                StaffIsDistributionT3,
                StaffIsAccountant,
                StaffIsTelemarketer,
            )
        else:
            self.available_permission_classes = (IsSuperUser,)
        return (CheckAnyPermission(),)

    lookup_fields = ["alias", "pk"]

    def get_queryset(self):
        order_items = StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            # organization=self.request.user.organization
        ).select_related(
            'primary_unit',
            'secondary_unit',
            'stock__store_point',
            'stock__product__manufacturing_company',
            'stock__product__form',
            'stock__product__subgroup__product_group',
            'stock__product__generic',
            'stock__product__primary_unit',
            'stock__product__secondary_unit',
            'stock__product__category',
            'stock__product__compartment',
        )
        order_filters = {
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER
        }

        orders = Purchase.objects.filter(
            **order_filters
        ).only(
            "id",
            "alias",
            "grand_total",
            "invoice_group_id",
        ).prefetch_related(
            Prefetch(
                "stock_io_logs",
                queryset=order_items,
            ),
        )
        return super().get_queryset().select_related(
            "order_by_organization",
            "order_by_organization__primary_responsible_person",
            "responsible_employee",
        ).prefetch_related(
            Prefetch(
                "orders",
                queryset=orders,
            ),
        ).only(
            "id",
            "alias",
            "additional_cost",
            "additional_cost_rate",
            "additional_discount",
            "additional_discount_rate",
            "current_order_status",
            "customer_comment",
            "customer_rating",
            "date",
            "delivery_date",
            "discount",
            "print_count",
            "round_discount",
            "sub_total",
            "organization_id",
            "responsible_employee__id",
            "responsible_employee__alias",
            "responsible_employee__phone",
            "responsible_employee__first_name",
            "responsible_employee__last_name",
            "responsible_employee__code",
            "responsible_employee__person_group",
            "responsible_employee__company_name",
            "order_by_organization__id",
            "order_by_organization__alias",
            "order_by_organization__address",
            "order_by_organization__status",
            "order_by_organization__active_issue_count",
            "order_by_organization__primary_mobile",
            "order_by_organization__delivery_sub_area",
            "order_by_organization__delivery_thana",
            "order_by_organization__geo_location",
            "order_by_organization__name",
            "order_by_organization__primary_responsible_person__id",
            "order_by_organization__primary_responsible_person__alias",
            "order_by_organization__primary_responsible_person__code",
            "order_by_organization__primary_responsible_person__phone",
            "order_by_organization__primary_responsible_person__first_name",
            "order_by_organization__primary_responsible_person__last_name",
        )

    def retrieve(self, request, *args, **kwargs):
        data = super().retrieve(request, *args, **kwargs).data
        data["discount_message"] = get_dynamic_discount_message(
            discount_percentage=data["additional_dynamic_discount_percentage"]
        )
        return Response(data)


class OrderInvoiceGroupStatusResponsiblePersonBulkCreate(CreateAPICustomView):
    permission_classes = (CheckAnyPermission,)

    def get_serializer_class(self):
        return OrderInvoiceGroupModelSerializer.StatusResponsiblePersonBulkCreate

    def get_permissions(self):
        request_data = self.request.data if self.request.data else {}
        if self.request.method == 'POST' and 'current_order_status' in request_data.keys() and request_data['current_order_status'] in [OrderTrackingStatus.CANCELLED, OrderTrackingStatus.REJECTED]:
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsTelemarketer,
                StaffIsDistributionT2,
                StaffIsDistributionT3,
                StaffIsFrontDeskProductReturn,
                StaffIsSalesManager,
            )
        elif (
            self.request.method == 'POST'
            and ('current_order_status' in request_data.keys()
            and request_data['current_order_status'] == OrderTrackingStatus.ON_THE_WAY)
            or 'responsible_employee' in request_data.keys()
            ):
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsDeliveryHub,
                StaffIsDistributionT2,
                StaffIsDistributionT3,
                StaffIsFrontDeskProductReturn,
                StaffIsSalesManager,
                StaffIsTelemarketer,
            )
        elif (self.request.method == 'POST' and 'current_order_status' in request_data.keys() and
            request_data['current_order_status'] in [OrderTrackingStatus.COMPLETED, OrderTrackingStatus.PARITAL_DELIVERED, OrderTrackingStatus.FULL_RETURNED]):
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsAccountant,
                StaffIsDistributionT2,
                StaffIsDistributionT3,
                StaffIsFrontDeskProductReturn,
                StaffIsSalesManager,
                StaffIsTelemarketer,
            )
        else:
            self.available_permission_classes = (
                StaffIsAdmin,
                StaffIsDistributionT2,
                StaffIsDistributionT3,
                StaffIsSalesManager,
            )
        return (CheckAnyPermission(),)

    # def prepare_order_tracking_data(self, order_id_list, order_status, remarks, failed_reason = None):
    #     order_tracking_data = []
    #     tracking_object = {
    #         "order_status": order_status,
    #         "remarks": remarks
    #     }
    #     if failed_reason:
    #         tracking_object['failed_delivery_reason'] = failed_reason
    #     for order_id in order_id_list:
    #         tracking_object['order'] = order_id
    #         order_tracking_data.append({**tracking_object})
    #     return order_tracking_data

    def create_order_tracking_data(
        self,
        order_id_list,
        order_status,
        remarks,
        failed_reason=None,
        entry_by_id=None
        ):
        tracking_object = {
            "order_status": order_status,
            "remarks": remarks,
            "entry_by_id": entry_by_id
        }
        if failed_reason:
            tracking_object['failed_delivery_reason'] = failed_reason
        # Create Order Tracking Instances
        for order_id in order_id_list:
            tracking_object['order_id'] = order_id
            OrderTracking.objects.create(**tracking_object)

    def populate_es_index(self, invoice_pk_list):
        _chunk_size = 30
        _number_of_operation = int((len(invoice_pk_list) / _chunk_size) + 1)

        _lower_limit = 0
        _upper_limit = _chunk_size
        for _ in range(0, _number_of_operation):
            pks = list(invoice_pk_list[_lower_limit:_upper_limit])
            # if not self.is_status_ready_to_deliver:
            custom_elastic_rebuild(
                'ecommerce.models.OrderInvoiceGroup',
                {'pk__in': pks}
            )
            custom_elastic_rebuild(
                'pharmacy.models.Purchase',
                {'invoice_group__id__in': pks}
            )
            update_es_index_for_related_invoices.apply_async(
                (pks, ),
                countdown=5,
                retry=True, retry_policy={
                    'max_retries': 10,
                    'interval_start': 0,
                    'interval_step': 0.2,
                    'interval_max': 0.2,
                }
            )
            _lower_limit = _upper_limit
            _upper_limit = _lower_limit + _chunk_size

    def update_organization_responsible_for_invoice_groups(self, invoice_group_pk_list, responsible_employee_id):
        from core.tasks import update_organization_responsible_employee_from_invoice_groups_on_bg

        _chunk_size = 20
        _number_of_operation = int((len(invoice_group_pk_list) / _chunk_size) + 1)

        _lower_limit = 0
        _upper_limit = _chunk_size
        for _ in range(0, _number_of_operation):
            pks = list(invoice_group_pk_list[_lower_limit:_upper_limit])
            update_organization_responsible_employee_from_invoice_groups_on_bg.apply_async(
                (pks, responsible_employee_id),
                countdown=5,
                retry=True, retry_policy={
                    'max_retries': 10,
                    'interval_start': 0,
                    'interval_step': 0.2,
                    'interval_max': 0.2,
                }
            )
            _lower_limit = _upper_limit
            _upper_limit = _lower_limit + _chunk_size

        organization_id_list = list(OrderInvoiceGroup.objects.filter(
            id__in=invoice_group_pk_list
        ).select_related('order_by_organization').values_list(
            'order_by_organization', flat=True
        ))
        update_organization_responsible_employee_from_organization_list.apply_async(
            (organization_id_list,),
            countdown=120,
            retry=True, retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )

    def get_error_message_for_older_invoice(self, invoice_list):
        message = ', '.join(map(str, invoice_list))
        if len(invoice_list) > 1:
            return f"{message} are"
        return f"{message} is"

    def post(self, request, *args, **kwargs):
        data = request.data
        referer = request.META.get('HTTP_APPLICATION', None)
        order_invoice_group_ids = data.get('order_invoice_group_ids', [])
        responsible_employee = data.get('responsible_employee', "")
        remarks = data.get('remarks', "")
        tracking_status = data.get("current_order_status", None) if data.get("current_order_status", None) else None
        is_status_ready_to_deliver = tracking_status == OrderTrackingStatus.READY_TO_DELIVER
        self.is_status_ready_to_deliver = is_status_ready_to_deliver
        failed_delivery_reason = data.get("failed_delivery_reason", None) if data.get("failed_delivery_reason", None) else None
        # If request is from reporter server use code to find entry by user
        entry_by_id = self.request.META.get('HTTP_ENTRY_BY_ID', '')
        if entry_by_id and checkers.is_integer(entry_by_id):
            entry_by_id = int(entry_by_id)
        else:
            entry_by_id = self.request.user.id

        try:
            with transaction.atomic():
                from core.utils import get_manager_for_employee

                if order_invoice_group_ids and (responsible_employee or tracking_status):
                    # Fetch invoice groups
                    order_invoice_group_ids = list(set(order_invoice_group_ids))
                    invoice_groups = OrderInvoiceGroup.objects.filter(
                        pk__in=order_invoice_group_ids,
                    )
                    update_fields_data = {}
                    extended_updated_fields = {}
                    if responsible_employee:
                        # Update organization responsible employee
                        self.update_organization_responsible_for_invoice_groups(
                            order_invoice_group_ids,
                            responsible_employee
                        )
                        update_fields_data['responsible_employee_id'] = responsible_employee
                        extended_updated_fields['secondary_responsible_employee_id'] = get_manager_for_employee(responsible_employee)
                    if tracking_status is not None:
                        days_of_old = 7
                        if referer and referer == 'reporting-backend':
                            # This Order Delivery Time is used in Invoice Groups to find out the time when porter delivered
                            extended_updated_fields['delivered_at'] = timezone.now()

                            days_of_old = 1.5
                        elif request.user.has_permission_for_changing_older_invoice_status():
                            days_of_old = 30
                        old_invoice_groups = invoice_groups.filter(
                            delivery_date__lte=timezone.now() - timedelta(days=days_of_old)
                        ).values_list('id', flat=True)
                        # Prevent invoice status change for delivery backend
                        if referer and referer == 'reporting-backend' and old_invoice_groups.exists():
                            old_invoice_groups = list(old_invoice_groups)
                            content = {
                                "error": f"Status change is not permitted. Invoice {self.get_error_message_for_older_invoice(old_invoice_groups)} 12 hours older."
                            }
                            return Response(content, status=status.HTTP_400_BAD_REQUEST)
                        # Prevent invoice status change for non super user
                        if old_invoice_groups.exists() and not request.user.is_superuser:
                            old_invoice_groups = list(old_invoice_groups)
                            content = {
                                "error": f"Status change is not permitted. Invoice {self.get_error_message_for_older_invoice(old_invoice_groups)} {days_of_old} days older."
                            }
                            return Response(content, status=status.HTTP_400_BAD_REQUEST)
                        update_fields_data['current_order_status'] = tracking_status
                    if failed_delivery_reason:
                        extended_updated_fields['failed_delivery_reason'] = failed_delivery_reason
                    update_fields_data['updated_by_id'] = entry_by_id

                    # Update invoice groups
                    invoice_groups.update(**update_fields_data, **extended_updated_fields)
                    # Delete qs count cache
                    delete_qs_count_cache(OrderInvoiceGroup)
                    # Fetch orders
                    orders = Purchase.objects.filter(
                        invoice_group__id__in=order_invoice_group_ids
                    ).only(
                        'responsible_employee_id',
                        'updated_by_id',
                        'current_order_status',
                    )
                    order_ids = orders.values_list("pk", flat=True)
                    order_ids = list(set(order_ids))
                    # Update order
                    orders.update(**update_fields_data)
                    # Added this for finding a bug related to invoice status change
                    send_invoice_status_change_log_to_mm.delay(
                        order_invoice_group_ids=order_invoice_group_ids,
                        responsible_employee=responsible_employee,
                        tracking_status=tracking_status,
                        entry_by_id=entry_by_id,
                        _timestamp=str(datetime.now())
                    )
                    # Create order tracking instances
                    if tracking_status is not None:
                        self.create_order_tracking_data(
                            order_ids,
                            tracking_status,
                            remarks,
                            failed_delivery_reason,
                            entry_by_id
                        )
                    # Delete redis cache
                    key_list = list(
                        map(
                            lambda item: 'purchase_distributor_order_{}'.format(str(item).zfill(12)),
                            order_ids
                        )
                    )

                    cache.delete_many(key_list)
                    # Populate ES doc without celery for status Ready To Delivery
                    if is_status_ready_to_deliver:
                        update_order_invoice_group_es_doc(
                            _queryset=invoice_groups
                        )

                    # Populate es index
                    self.populate_es_index(order_invoice_group_ids)
                    response = {
                        'message': 'Success',
                        'orders': list(order_ids)
                    }
                    return Response(
                        # response.data,
                        response,
                        status=status.HTTP_201_CREATED
                    )
                content = {'error': "Missing order invoice group ids"}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class ResponsibleEmployeeWiseInvoiceGroupDeliverySheetList(generics.ListAPIView):
    """
        Report to show distributor order invoice group delivery sheet
        for given filters
    """
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsDeliveryHub,
        StaffIsSalesManager,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ResponsibleEmployeeWiseInvoiceGroupDeliverySheetSerializer
    filterset_class = OrderInvoiceGroupListFilter
    pagination_class = CachedCountPageNumberPagination

    def get_queryset(self):
        invoice_groups = OrderInvoiceGroup.objects.filter(
            status=Status.ACTIVE,
            organization__id=self.request.user.organization_id,
            orders__isnull=False
        ).values(
            'order_by_organization',
            'order_by_organization__alias',
            'order_by_organization__name',
            'order_by_organization__primary_mobile',
            'order_by_organization__address'
        ).annotate(
            unique_item=Count(Case(When(
                orders__stock_io_logs__status=Status.DISTRIBUTOR_ORDER,
                then=F('orders__stock_io_logs__stock'))), distinct=True),
            total_item=Coalesce(Sum(Case(When(
                orders__stock_io_logs__status=Status.DISTRIBUTOR_ORDER,
                then=F('orders__stock_io_logs__quantity')))), 0.00),
            order_invoice_group_ids=ArrayAgg(Cast('pk', IntegerField()), distinct=True),
            order_invoice_group_count=ArrayLength('order_invoice_group_ids'),
            order_invoice_group_amounts=JSONBAgg(
                Func(
                    Value('id'), 'id',
                    Value('orders'), 'orders',
                    Value('sub_total'), 'sub_total',
                    Value('additional_discount'), 'additional_discount',
                    Value('additional_cost'), 'additional_cost',
                    Value('discount'), 'discount',
                    Value('round_discount'), 'round_discount',
                    function='jsonb_build_object'
                ),
                ordering=('pk'),
            ),
        )
        return invoice_groups


class CloneOrderInvoiceGroup(APIView):

    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsTelemarketer,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsSalesManager,
        StaffIsDeliveryHub
    )
    permission_classes = (CheckAnyPermission,)

    @transaction.atomic
    def post(self, request):

        try:
            invoice_group_alias = request.data.get('alias', '')
            invoice_group_id = request.data.get('id', '')
            delivery_date_ecom = request.data.get('delivery_date_ecom', '')
            delivery_date = request.data.get('delivery_date', '')
            if invoice_group_alias:
                order_invoice_group = OrderInvoiceGroup.objects.only("id").get(alias=invoice_group_alias)
            elif invoice_group_id:
                order_invoice_group = OrderInvoiceGroup.objects.only("id").get(id=invoice_group_id)
            else:
                error_response = {
                    "status": "error",
                    "message": "Invoice Group id or alias required."
                }
                return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
            is_valid_for_clone, existing_instance = order_invoice_group.is_valid_for_clone()
            if not is_valid_for_clone:
                error_response = {
                    "status": "error",
                    "message": f"Existing Invoice Group({existing_instance.id}) found."
                }
                return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
            # If request is from reporter server use code to find entry by user
            entry_by_id = self.request.META.get('HTTP_ENTRY_BY_ID', '')
            if entry_by_id and checkers.is_integer(entry_by_id):
                entry_by_id = int(entry_by_id)
            else:
                entry_by_id = self.request.user.id
            if not delivery_date_ecom:
                current_date = datetime.now()
                new_delivery_date = get_tentative_delivery_date(current_date)
                delivery_date = str(new_delivery_date)
            else:
                delivery_date = delivery_date_ecom
            old_order_invoice_group_id, new_order_invoice_group_id = order_invoice_group.clone_invoice_group(
                delivery_date,
                entry_by_id
            )
            response_data = {
                "status": "Ok",
                "message": f"Successfully cloned order invoice group #{old_order_invoice_group_id} as #{new_order_invoice_group_id}"
            }
            # Delete qs count cache
            delete_qs_count_cache(OrderInvoiceGroup)

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class CustomerOrderStatistics(ListAPIView):
    available_permission_classes = (AnyLoggedInUser, )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        period = request.query_params.get('period', '')
        valid_statuses = [
            OrderTrackingStatus.DELIVERED,
            OrderTrackingStatus.COMPLETED,
            OrderTrackingStatus.PARITAL_DELIVERED,
            OrderTrackingStatus.PORTER_DELIVERED,
            OrderTrackingStatus.PORTER_PARTIAL_DELIVERED,
        ]

        queryset = OrderInvoiceGroup.objects.filter(
            status=Status.ACTIVE,
            order_by_organization__id=self.request.user.organization_id,
            orders__isnull=False,
            current_order_status__in=valid_statuses
        ).distinct()

        if period:
            start_date, end_date = get_date_range_from_period(period, False, False)
            queryset = queryset.filter(
                delivery_date__range=[
                    start_date,
                    end_date
                ]
            )

        invoice_groups = OrderInvoiceGroupListFilter(request.GET, queryset).qs

        invoice_groups_pk = invoice_groups.values_list('pk', flat=True)

        total_invoice_amount = invoice_groups.aggregate(
            total_amount=Coalesce(
                Sum('sub_total'), decimal.Decimal(0)
            ) - Coalesce(
                Sum('discount'), decimal.Decimal(0)
            ) - Coalesce(
                Sum('additional_discount'), decimal.Decimal(0)
            ) + Coalesce(
                Sum('round_discount'), decimal.Decimal(0)
            ) + Coalesce(
                Sum('additional_cost'), decimal.Decimal(0)
            ),
        ).get('total_amount', 0)

        total_short_return_amount = ShortReturnLog.objects.filter(
            status=Status.ACTIVE,
            invoice_group_id__in=invoice_groups_pk
        ).aggregate(
            total_amount=Coalesce(Sum(F('short_return_amount') + F('round_discount')), decimal.Decimal(0))
        ).get('total_amount', 0)

        order_io_log_data = StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            purchase__invoice_group_id__in=invoice_groups_pk
        ).order_by().aggregate(
            total_discount=Coalesce(Sum('discount_total'), 0.00),
            total_qty=Coalesce(Sum('quantity'), 0.00),
            total_unique_item=Count('stock_id', distinct=True),
            total_unique_company=Count('stock__product__manufacturing_company_id', distinct=True)
        )
        order_total_discount = order_io_log_data.get('total_discount', 0)
        total_order_qty = order_io_log_data.get('total_qty', 0)
        total_unique_product = order_io_log_data.get('total_unique_item', 0)
        total_unique_company = order_io_log_data.get('total_unique_company', 0)

        short_return_item_data = ShortReturnItem.objects.filter(
            status=Status.ACTIVE,
            short_return_log__invoice_group_id__in=invoice_groups_pk
        ).aggregate(
            total_discount=Coalesce(Sum('discount_total'), decimal.Decimal(0)),
            total_qty=Coalesce(Sum('quantity'), decimal.Decimal(0))
        )
        short_return_total_discount = short_return_item_data.get('total_discount', 0)
        total_discount = order_total_discount - float(short_return_total_discount)

        total_short_return_qty = short_return_item_data.get('total_qty', 0)

        margin = 12.5
        net_purchase = round(float(total_invoice_amount - total_short_return_amount), 2)
        if not net_purchase:
            response_data = {
                'net_purchase': net_purchase,
                'net_discount': 0,
                'net_discount_percentage': 0,
                'ordered_quantity': 0,
                'estimated_additional_profit': 0,
                'total_unique_product': 0,
                'total_unique_company': 0,
                'days_received_orders': 0
            }
            return Response(response_data, status=status.HTTP_200_OK)

        net_discount = round(total_discount, 2)
        net_discount_percentage = round((net_discount * 100 / net_purchase), 2)
        ordered_quantity = total_order_qty - float(total_short_return_qty)
        estimated_profit = round((net_discount - ((net_purchase + net_discount) / 100) * margin), 2)
        days_received_orders = invoice_groups.values('delivery_date')

        response_data = {
            'net_purchase': net_purchase,
            'net_discount': net_discount,
            'net_discount_percentage': net_discount_percentage,
            'ordered_quantity': ordered_quantity,
            'estimated_additional_profit': estimated_profit,
            'total_unique_product': total_unique_product,
            'total_unique_company': total_unique_company,
            'days_received_orders': days_received_orders.count()
        }
        return Response(response_data, status=status.HTTP_200_OK)


class InvoiceGroupListByProduct(ListAPICustomView):
    """
    Fetching invoices by choosing a product
    """
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsDistributionT1,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsDeliveryHub,
        StaffIsSalesManager,
        StaffIsTelemarketer,
        StaffIsFrontDeskProductReturn,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = OrderInvoiceGroupModelSerializer.ListWithProductQuantity
    filterset_class = OrderInvoiceGroupListFilter
    pagination_class = CachedCountPageNumberPagination

    def get_queryset(self):
        product_alias = self.request.query_params.get('product', None)
        if not product_alias:
            return OrderInvoiceGroup.objects.none()
        queryset = super().get_queryset().filter(
            orders__stock_io_logs__stock__product__alias=product_alias
        ).annotate(
            total_quantity=Sum('orders__stock_io_logs__quantity'),
        ).select_related(
            'responsible_employee',
            'order_by_organization',
            'order_by_organization__entry_by',
        ).prefetch_related(
            'orders',
        ).distinct()

        return queryset.order_by('-pk')


class InvoiceGroupProductSumList(APIView):
    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )

    def get(self, request, *args, **kwargs):
        delivery_date_from = request.query_params.get("delivery_date_from", None)
        delivery_date_to = request.query_params.get("delivery_date_to", None)
        responsible_employee = request.query_params.get("responsible_employee", None)
        area = request.query_params.get("area", None)
        sub_area = request.query_params.get("sub_area", None)

        if not (delivery_date_from and delivery_date_to) and not responsible_employee and not area and not sub_area:
            return Response(
                {"message": "At least one filter is required to get result"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
        )

        if delivery_date_from and delivery_date_to:
            queryset = queryset.filter(
                purchase__invoice_group__delivery_date__range=[delivery_date_from,delivery_date_to],
            )
        if responsible_employee:
            queryset = queryset.filter(
                purchase__invoice_group__responsible_employee__id=responsible_employee,
            )
        if area:
            queryset = queryset.filter(
                purchase__invoice_group__order_by_organization__delivery_thana=area,
            )
        if sub_area:
            queryset = queryset.filter(
                purchase__invoice_group__order_by_organization__delivery_sub_area=sub_area,
            )

        queryset = queryset.values(
            "stock__id",
        ).annotate(
            product_name = Concat(F("stock__product__form"), Value(" "), F("stock__product__full_name"),output_field=CharField()),
            product_sum=Sum("quantity"),
            product_short=Coalesce(
                Sum(
                    Case(
                        When(stock_io_short_return__short_return_log__type=ShortReturnLogType.SHORT, then="stock_io_short_return__short_return_log__total_short_return_items"),
                        default=0.0,
                        output_field=FloatField()
                    )
                ),
                0.0,
                output_field=FloatField()
            ),
            product_return=Coalesce(
                Sum(
                    Case(
                        When(stock_io_short_return__short_return_log__type=ShortReturnLogType.RETURN, then="stock_io_short_return__short_return_log__total_short_return_items"),
                        default=0.0,
                        output_field=FloatField()
                    )
                ),
                0.0,
                output_field=FloatField()
            ),
        )
        serializer = InvoiceGroupProductSumSerializer(queryset, many=True)

        return Response({"results": serializer.data}, status=status.HTTP_200_OK)


class InvoiceGroupProductQuantityWithInvoiceCountReport(APIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
    )
    permission_classes = (CheckAnyPermission, )

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        area = request.query_params.get("area", None)
        current_order_status = request.query_params.get("current_order_status", None)
        # delivery_date = request.query_params.get("delivery_date", today)
        delivery_hub = request.query_params.get("delivery_hub", None)
        order_type = request.query_params.get("order_type", None)
        responsible_employee = request.query_params.get("responsible_employee", None)
        start_delivery_date = request.query_params.get("date_0", None)
        end_delivery_date = request.query_params.get("date_1", None)
        area_code = request.query_params.get("area_code", "")

        queryset = StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
        )
        if current_order_status:
            queryset = queryset.filter(
                purchase__invoice_group__current_order_status__in=current_order_status.split(",")
            )
        else:
            queryset = queryset.exclude(
                Q(purchase__invoice_group__current_order_status=OrderTrackingStatus.CANCELLED) |
                Q(purchase__invoice_group__current_order_status=OrderTrackingStatus.REJECTED)
            )

        if area:
            queryset = queryset.filter(
                purchase__invoice_group__order_by_organization__delivery_thana__in=area.split(","),
            )
        if start_delivery_date and end_delivery_date:
            queryset = queryset.filter(
                purchase__invoice_group__delivery_date__range=(start_delivery_date, end_delivery_date)
            )
        if delivery_hub:
            queryset = queryset.filter(
                purchase__invoice_group__order_by_organization__delivery_hub__alias__in=delivery_hub.split(","),
            )
        if order_type and order_type == 'regular':
            queryset = queryset.filter(
                purchase__is_queueing_order=False,
            )
        if order_type and order_type == 'pre_order':
            queryset = queryset.filter(
                purchase__is_queueing_order=True,
            )
        if responsible_employee:
            queryset = queryset.filter(
                purchase__invoice_group__responsible_employee__alias=responsible_employee,
            )
        if area_code:
            queryset = queryset.filter(
                organization__area__code__in=area_code.split(",")
            )

        queryset = queryset.values(
            "stock__id",
            "stock__product__compartment__id",
        ).annotate(
            product_name=Concat(F("stock__product__form__name"), Value(" "), F("stock__product__full_name"),output_field=CharField()),
            company_name=F("stock__product__manufacturing_company__name"),
            product_quantity=Sum("quantity"),
            invoice_count=Count("purchase__invoice_group", distinct=True),
            mrp=F("stock__product__trading_price"),
            compartment=ArrayAgg(
                JSONObject(
                    id=Coalesce(F("stock__product__compartment__id"), Value(0)),
                    alias=Coalesce(F("stock__product__compartment__alias"), Value(UUID(int=0))),
                    name=Coalesce(F("stock__product__compartment__name"), Value("")),
                    priority=Coalesce(F("stock__product__compartment__priority"), Value(0))
                ),
                distinct=True,
            )

        ).order_by("stock__product__compartment__priority", "stock__product__full_name")
        serializer = InvoiceGroupProductQuantityInvoiceCountSerializer(queryset, many=True)

        return Response({"results": serializer.data}, status=status.HTTP_200_OK)


class InvoiceGroupStatusChangeLog(ListAPIView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsTelemarketer,
        StaffIsDeliveryHub,
        StaffIsFrontDeskProductReturn,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsSalesCoordinator,
        StaffIsSalesManager,
    )
    permission_classes = (CheckAnyPermission,)
    lookup_fields = ["alias"]
    serializer_class = OrderTrackingModelSerializer.ListWithEntryBy
    pagination_class = CachedCountPageNumberPagination

    def get_queryset(self):
        order_invoice_group_alias = self.kwargs.get('alias', None)
        get_orders_from_invoice = OrderInvoiceGroup.objects.filter(
            alias=order_invoice_group_alias,
            status=Status.ACTIVE
        ).values_list('orders', flat=True)
        get_orders_tracking_queryset = OrderTracking.objects.filter(
            order__invoice_group__alias=order_invoice_group_alias,
            order__id=get_orders_from_invoice[0]
        ).select_related(
            "entry_by",
        ).only(
            "id",
            "alias",
            "date",
            "remarks",
            "order_id",
            "failed_delivery_reason",
            "order_status",
            "entry_by__id",
            "entry_by__alias",
            "entry_by__code",
            "entry_by__phone",
            "entry_by__first_name",
            "entry_by__last_name",
        ).order_by('id')
        return get_orders_tracking_queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if queryset:
            serializer = self.get_serializer(queryset, many=True)
            response = {
                "total_order_tracking_status":queryset.count(),
                "order_tracking_status_data":serializer.data
            }
            return Response(response, status=status.HTTP_200_OK)
        else:
            error_response = {
                "status": "error",
                "message": "Invalid UUID"
            }
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)


class InvoiceGroupAdditionalDiscountMismatch(APIView):
    """
    Fetching invoices by choosing a date or invoices ID
    """
    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        date = request.query_params.get('delivery_date', datetime.now().date())
        if not date:
            return Response({'detail': 'Delivery Date is required'}, status=status.HTTP_400_BAD_REQUEST)
        # check date format
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
            return Response(
                {'detail': 'Delivery Date format should be yyyy-mm-dd'},
                status=status.HTTP_400_BAD_REQUEST
            )
        minimum_order_amount = get_minimum_order_amount()
        queryset = OrderInvoiceGroup.objects.filter(
            status=Status.ACTIVE,
            delivery_date=date
        ).annotate(
            total_amount=F('sub_total') - F('discount'),
        ).filter(
            total_amount__gte=minimum_order_amount,
        ).values(
            'id',
            'total_amount',
            'additional_discount',
            'additional_discount_rate'
        )
        response_data = []
        for query in queryset:
            total_amount = float(query['total_amount'])
            discount = get_discount_for_cart_and_order_items(total_amount, rounding_off=False)
            discount_percentage = float(round(discount.get('current_discount_percentage'), 2))
            discount_amount = float(round(discount.get('current_discount_amount'), 3))
            additional_discount_rate = float(round(query['additional_discount_rate'], 2))
            additional_discount = float(round(query['additional_discount'], 3))
            if (discount_percentage != additional_discount_rate) or (abs(discount_amount - additional_discount) > 0.5):
                response_data.append({
                    'id': query['id'],
                    'total_amount': total_amount,
                    'current': {
                        'additional_discount_rate': query['additional_discount_rate'],
                        'additional_discount': query['additional_discount'],
                    },
                    'expected': {
                        'additional_discount_rate': discount_percentage,
                        'additional_discount': discount_amount,
                    }
                })
        if response_data:
            return Response(response_data, status=status.HTTP_200_OK)
        return Response({'detail': 'No mismatch found!!!'}, status=status.HTTP_200_OK)

    def post(self, request):
        request_data = request.data
        # check if request data is empty
        if not request_data:
            return Response({'detail': 'Please provide delivery_date or invoices_id'}, status=status.HTTP_400_BAD_REQUEST)
        # check if date  or invoices_id exist in request data
        if 'delivery_date' not in request_data and 'invoices_id' not in request_data:
            return Response({'detail': 'Please provide delivery_date or invoices_id'}, status=status.HTTP_400_BAD_REQUEST)
        filters = {}
        if 'invoices_id' in request_data and 'delivery_date' in request_data:
            filters['delivery_date'] = request_data['delivery_date']
            filters['id__in'] = request_data['invoices_id']
        elif 'delivery_date' in request_data:
            filters['delivery_date'] = request_data['delivery_date']
        elif 'invoices_id' in request_data:
            filters['id__in'] = request_data['invoices_id']

        minimum_order_amount = get_minimum_order_amount()
        queryset = OrderInvoiceGroup.objects.filter(
            status=Status.ACTIVE,
            **filters
        ).annotate(
            total_amount=Coalesce(Round(F('sub_total') - F('discount')), decimal.Decimal(0)),
        ).filter(
            total_amount__gte=minimum_order_amount,
        ).values(
            'id',
            'orders__id',
            'sub_total',
            'discount',
            'total_amount',
            'additional_discount',
            'additional_discount_rate'
        )
        response_data = update_invoice_group_additional_discount_amount(queryset)
        if response_data:
            return Response(
                response_data,
                status=status.HTTP_200_OK
            )
        return Response(
            {'detail': 'No invoices are found to fix'},
            status=status.HTTP_200_OK
        )


class InvoiceGroupStatusReport(ListAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsSalesCoordinator,
        StaffIsSalesManager,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsDeliveryHub,
    )
    permission_classes = (CheckAnyPermission,)
    filterset_class = OrderInvoiceGroupListFilter
    serializer_class = OrderInvoiceGroupModelSerializer.StatusReport

    def get_queryset(self):
        query_params = self.request.query_params

        filters = {
            'status': Status.ACTIVE,
        }
        if len(query_params) == 0:
            filters['delivery_date'] = datetime.today()

        queryset = OrderInvoiceGroup.objects.filter(
            **filters
        ).values(
            'responsible_employee'
        ).annotate(
            delivery_date=Cast('delivery_date', DateField()),
            porter_code=F('responsible_employee__code'),
            full_name=Concat(
                Cast('responsible_employee__first_name', CharField()),
                Value(' '),
                Cast('responsible_employee__last_name', CharField()),
            ),
            assigned_total=Count('id'),
            accepted=Count(Case(When(
                current_order_status=OrderTrackingStatus.ACCEPTED,
                then=F('id')
            ), output_field=IntegerField())),
            ready_to_deliver=Count(Case(When(
                current_order_status=OrderTrackingStatus.READY_TO_DELIVER,
                then=F('id')
            ), output_field=IntegerField())),
            on_the_way=Count(Case(When(
                current_order_status=OrderTrackingStatus.ON_THE_WAY,
                then=F('id')
            ), output_field=IntegerField())),
            delivered=Count(Case(When(
                current_order_status=OrderTrackingStatus.DELIVERED,
                then=F('id')
            ), output_field=IntegerField())),
            completed=Count(Case(When(
                current_order_status=OrderTrackingStatus.COMPLETED,
                then=F('id')
            ), output_field=IntegerField())),
            rejected=Count(Case(When(
                current_order_status=OrderTrackingStatus.REJECTED,
                then=F('id')
            ), output_field=IntegerField())),
            cancelled=Count(Case(When(
                current_order_status=OrderTrackingStatus.CANCELLED,
                then=F('id')
            ), output_field=IntegerField())),
            partial_delivered=Count(Case(When(
                current_order_status=OrderTrackingStatus.PARITAL_DELIVERED,
                then=F('id')
            ), output_field=IntegerField())),
            full_returned=Count(Case(When(
                current_order_status=OrderTrackingStatus.FULL_RETURNED,
                then=F('id')
            ), output_field=IntegerField())),
            in_queue=Count(Case(When(
                current_order_status=OrderTrackingStatus.IN_QUEUE,
                then=F('id')
            ), output_field=IntegerField())),
            porter_delivered=Count(Case(When(
                current_order_status=OrderTrackingStatus.PORTER_DELIVERED,
                then=F('id')
            ), output_field=IntegerField())),
            porter_full_return=Count(Case(When(
                current_order_status=OrderTrackingStatus.PORTER_FULL_RETURN,
                then=F('id')
            ), output_field=IntegerField())),
            porter_partial_delivered=Count(Case(When(
                current_order_status=OrderTrackingStatus.PORTER_PARTIAL_DELIVERED,
                then=F('id')
            ), output_field=IntegerField())),
            porter_failed_delivered=Count(Case(When(
                current_order_status=OrderTrackingStatus.PORTER_FAILED_DELIVERED,
                then=F('id')
            ), output_field=IntegerField())),
            rating_count=Count(Case(When(
                customer_rating__gt=0,
                then=F('id')
            ), output_field=IntegerField())),
            rating_count_of_one=Count(Case(When(
                customer_rating=1,
                then=F('id')
            ), output_field=IntegerField())),
            rating_count_of_two=Count(Case(When(
                customer_rating=2,
                then=F('id')
            ), output_field=IntegerField())),
            rating_count_of_three=Count(Case(When(
                customer_rating=3,
                then=F('id')
            ), output_field=IntegerField())),
            rating_count_of_four=Count(Case(When(
                customer_rating=4,
                then=F('id')
            ), output_field=IntegerField())),
            rating_count_of_five=Count(Case(When(
                customer_rating=5,
                then=F('id')
            ), output_field=IntegerField())),
        ).order_by('responsible_employee')

        return queryset
