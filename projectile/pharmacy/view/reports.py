import json
import time
from datetime import datetime
from datetime import date
from validator_collection import checkers
from django.core.serializers.json import DjangoJSONEncoder
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
)
from django.db.models.functions import Coalesce, Cast
from django.utils import timezone
from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from common.helpers import prepare_start_date_end_date
from common.utils import (
    get_datetime_obj_from_datetime_str,
    prepare_start_date, prepare_end_date,
    not_blank,
)
from common.enums import Status, ReportType
from core.permissions import (
    StaffIsAdmin,
    StaffIsProcurementManager,
    StaffIsProcurementOfficer,
    StaffIsReceptionist,
    StaffIsAccountant,
    StaffIsLaboratoryInCharge,
    StaffIsNurse,
    StaffIsPhysician,
    StaffIsSalesman,
    CheckAnyPermission,
    IsSuperUser,
    StaffIsDistributionT3,
    StaffIsDistributionT2,
    StaffIsSalesManager,
    StaffIsProcurementCoordinator,
)
from core.views.common_view import(
    ListAPICustomView
)

from core.enums import PriceType
from core.models import PersonOrganization
from account.models import Transaction, Accounts
from account.enums import TransactionFor
from ..custom_serializer.stock import (
    ProductWiseDistributorOrderDiscountSummarySerializer,
    MismatchedStockWithIOSerializer,
)
from ..custom_serializer.purchase import (
    DateAndStatusWiseOrderAmountSerializer,
    ResponsibleEmployeeWiseDeliverySheetSerializer,
)
from ..custom_serializer.stock_io_log import ProductWiseStockTransferReportSerializer
from ..models import OrderTracking, Sales, Purchase, Stock, StockIOLog
from ..enums import (
    SalesType,
    StockIOType,
    OrderTrackingStatus,
    DistributorOrderType,
    PurchaseType,
)
from ..utils import filter_data_by_user_permitted_store_points
from ..filters import (
    DateAndStatusWiseOrderAmountListFilter,
    DistributorOrderProductSummaryFilter,
    DistributorOrderProductSummaryIOFilter,
    DistributorOrderListFilter,
    ProductWiseStockTransferReportFilter,
    MismatchedStockWithIOProductListFilter,
)


class Round(Func):
    function = "ROUND"
    template = "%(function)s(%(expressions)s::numeric, 2)"
    # arity = 2


class ArrayLength(Func):
    function = 'CARDINALITY'


class SalesPurchaseStockValueGroupWiseSummary(generics.ListAPIView):
    """Report to show sales, purchase and stock value summary
        for given date range of a selected StorePoint
    """
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission,)
    pagination_class = None

    def get(self, request):
        start_date = self.request.query_params.get('date_0', None)
        start_date = start_date if start_date else str(date.today())
        end_date = self.request.query_params.get('date_1', None)
        end_date = end_date if end_date else str(date.today())
        store_points = self.request.query_params.get('store_point', None)
        report_type = self.request.query_params.get(
            'report_type', ReportType.GROUP_WISE_SALE_SUMMARY)
        try:
            report_type = int(report_type)
        except ValueError:
            report_type = ReportType.GROUP_WISE_SALE_SUMMARY

        if report_type not in [ReportType.GROUP_WISE_SALE_SUMMARY, ReportType.GROUP_WISE_PURCHASE_SUMMARY, ReportType.GROUP_WISE_STOCK_VALUE_SUMMARY]:
            return Response(StockIOLog.objects.none())
        start_date_time = prepare_start_date(
            start_date
        )
        end_date_time = prepare_end_date(
           end_date
        )
        extra_filters = {}
        values = {
            'organization': self.request.user.organization_id,
            'status': Status.ACTIVE
        }
        store_point_list = []
        if store_points:
            # prepare store points alias list after validating uuid
            store_point_list = list(filter(not_blank(), store_points.split(',')))
        if report_type == ReportType.GROUP_WISE_SALE_SUMMARY:
            extra_filters = {
                'sales__sale_date': "date(sale_date AT TIME ZONE '{0}')".format(
                    timezone.get_current_timezone())
            }
            values['sales__sale_date__range'] = [start_date_time, end_date_time]
            if store_point_list:
                values['sales__store_point__alias__in'] = store_point_list

        elif report_type == ReportType.GROUP_WISE_PURCHASE_SUMMARY:
            extra_filters = {
                'purchase__purchase_date': "date(purchase_date AT TIME ZONE '{0}')".format(
                    timezone.get_current_timezone())
            }
            values['purchase__purchase_date__range'] = [start_date_time, end_date_time]
            if store_point_list:
                values['purchase__store_point__alias__in'] = store_point_list

        elif report_type == ReportType.GROUP_WISE_STOCK_VALUE_SUMMARY:
            # values['purchase__purchase_date__range'] = [start_date_time, end_date_time]
            if store_point_list:
                values['store_point__alias__in'] = store_point_list

        # elif report_type == ReportType.GROUP_WISE_STOCK_VALUE_SUMMARY:
        #     extra_filters = {
        #         'purchase__purchase_date': "date(purchase_date AT TIME ZONE '{0}')".format(
        #             timezone.get_current_timezone())
        #     }
        #     values['purchase__purchase_date__range'] = [start_date_time, end_date_time]
        #     if store_point_list:
        #         values['purchase__store_point__alias__in'] = store_point_list
        arguments = {}
        for key, value in values.items():
            if value is not None:
                arguments[key] = value

        if report_type == ReportType.GROUP_WISE_STOCK_VALUE_SUMMARY:
            queryset = Stock.objects.filter(
                **arguments,
            ).order_by()
        else:
            queryset = StockIOLog().get_all_actives().filter(
                **arguments
            ).extra(
                select=extra_filters
            ).order_by()
        if report_type == ReportType.GROUP_WISE_SALE_SUMMARY:
            queryset = queryset.values(
                'stock__product__subgroup__product_group__name', 'sales__sale_date'
            ).annotate(
                # product_group=F('stock__product__subgroup__product_group__name'),
                sub_total=Coalesce(Sum(Case(
                    When(secondary_unit_flag=True, then=(
                        F('rate') / F('conversion_factor')
                    ) * F('quantity')),
                    When(secondary_unit_flag=False, then=(
                        F('quantity') * F('rate'))),
                    output_field=FloatField(),
                ) + F('round_discount') + F('vat_total')), 0.00),
                total_discount=Coalesce(Sum(F('discount_total')), 0.00),
            )

        elif report_type == ReportType.GROUP_WISE_PURCHASE_SUMMARY:
            queryset = queryset.values(
                'stock__product__subgroup__product_group__name', 'purchase__purchase_date'
            ).annotate(
                # product_group=F('stock__product__subgroup__product_group__name'),
                sub_total=Coalesce(Sum(Case(
                    When(secondary_unit_flag=True, then=(
                        F('rate') / F('conversion_factor')
                    ) * F('quantity')),
                    When(secondary_unit_flag=False, then=(
                        F('quantity') * F('rate'))),
                    output_field=FloatField(),
                ) + F('round_discount') + F('vat_total')), 0.00),
                total_discount=Coalesce(Sum(F('discount_total')), 0.00),
            )

        elif report_type == ReportType.GROUP_WISE_STOCK_VALUE_SUMMARY:
            queryset = queryset.values(
                'product__subgroup__product_group__name',
            ).annotate(
                # product_group=F('stock__product__subgroup__product_group__name'),
                sub_total=Sum(F('stock') * Case(
                    When(
                        organization__organizationsetting__purchase_price_type=PriceType.PRODUCT_PRICE,
                        then=F('product__purchase_price')
                    ),
                    When(
                        organization__organizationsetting__purchase_price_type=PriceType.LATEST_PRICE_AND_PRODUCT_PRICE,
                        purchase_rate__lte=0,
                        then=F('product__purchase_price')
                    ),
                    When(
                        organization__organizationsetting__purchase_price_type=PriceType.PRODUCT_PRICE_AND_LATEST_PRICE,
                        product__purchase_price__gt=0,
                        then=F('product__purchase_price')
                    ),
                    default=F('calculated_price'),
                ),
                )
            )

        return Response(queryset)


class DistributorOrderProductSummary(generics.ListAPIView):
    """Report to show product summary of accepted
        order of a distributor
    """
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementOfficer,
        StaffIsDistributionT3,
        StaffIsDistributionT2,
        StaffIsSalesManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        current_order_status = self.request.query_params.get(
            'current_order_status', None)
        area_code = self.request.query_params.get(
            "area_code", ""
        )
        if current_order_status:
            current_order_status = [int(item) for item in current_order_status.split(',') if item.isdigit() \
                and int(item) in OrderTrackingStatus.get_values()]
        else:
            current_order_status = [
                status
                for status in OrderTrackingStatus.get_values()
                if status
                not in [OrderTrackingStatus.CANCELLED, OrderTrackingStatus.REJECTED]
            ]
        filters = {
            "status": Status.DISTRIBUTOR_ORDER,
            "purchase__distributor": self.request.user.organization_id,
            "purchase__distributor_order_type": DistributorOrderType.ORDER,
            "purchase__purchase_type": PurchaseType.VENDOR_ORDER,
            "purchase__current_order_status__in": current_order_status,
        }

        if area_code:
            filters["organization__area__code__in"] = area_code.split(",")

        order_count = Purchase.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            distributor=self.request.user.organization_id,
            distributor_order_type=DistributorOrderType.ORDER,
            purchase_type=PurchaseType.VENDOR_ORDER,
            current_order_status__in=current_order_status,
        )
        order_count = DistributorOrderProductSummaryFilter(request.GET, order_count).qs

        io_logs = StockIOLog.objects.filter(**filters).order_by()
        io_logs = DistributorOrderProductSummaryIOFilter(request.GET, io_logs).qs
        io_logs = io_logs.values('stock').annotate(
            total_quantity=Coalesce(Sum(F('quantity')), 0.00),
            order_count=Count('purchase__id'),
            product_name=F('stock__product__full_name'),
            company_name=F('stock__product__manufacturing_company__name'),
            product_unit_name=Case(
                When(secondary_unit_flag=True, then=(
                    F('stock__product__secondary_unit__name'))),
                default=F('stock__product__primary_unit__name'),
            ),
            minimum_stock=F('stock__minimum_stock')
        ).filter().order_by(
            'stock__product__full_name',
            'stock__product__manufacturing_company__name'
        )

        DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
        _datetime_now = datetime.strptime(
            time.strftime(DATE_TIME_FORMAT, time.localtime()), DATE_TIME_FORMAT)

        return Response(
            {
                "current_date": _datetime_now,
                "order_count": order_count.count(),
                "product_summary": io_logs,
            }
        )


class ProductWiseDistributorOrderDiscountSummary(ListAPICustomView):

    """ When Date is not Selected Default date will be Today """

    permission_classes = (IsSuperUser, )
    serializer_class = ProductWiseDistributorOrderDiscountSummarySerializer
    pagination_class = None

    def get_queryset(self):
        stock_alias = self.kwargs.get('stock_alias', '')
        if stock_alias:
            queryset_template = '''SELECT product_full_name,
                                stock_io_info.*
                            FROM   (SELECT stock_id           AS id,
                                        DATE               AS order_date,
                                        Count(purchase_id) AS number_of_order,
                                        Avg(discount_rate) AS discount,
                                        SUM(quantity)      AS quantity
                                    FROM   (SELECT stock_id,
                                                purchase_id,
                                                DATE,
                                                quantity,
                                                discount_rate
                                            FROM   (SELECT id AS purchase_id
                                                    FROM   (SELECT order_id AS id
                                                            FROM   pharmacy_ordertracking po
                                                            WHERE  order_status = {0}
                                                                AND created_at > current_date - interval
                                                                                    '180'
                                                                                                day) AS
                                                        data
                                                        left join pharmacy_purchase USING(id)) AS
                                                purchase_data
                                                left join pharmacy_stockiolog USING(purchase_id)) AS data
                                    GROUP  BY stock_id,
                                            order_date) AS stock_io_info
                                left join pharmacy_stock USING(id)
                            WHERE  organization_id = {1} AND
                                    alias = '{2}'
                            ORDER  BY order_date DESC,
                                    number_of_order DESC,
                                    quantity DESC,
                                    product_full_name '''

            queryset_template = queryset_template.format(
                OrderTrackingStatus.COMPLETED, self.request.user.organization_id, stock_alias
            )
        else:
            queryset_template = '''SELECT product_full_name,
                                stock_io_info.*
                            FROM   (SELECT stock_id           AS id,
                                        DATE               AS order_date,
                                        Count(purchase_id) AS number_of_order,
                                        Avg(discount_rate) AS discount,
                                        SUM(quantity)      AS quantity
                                    FROM   (SELECT stock_id,
                                                purchase_id,
                                                DATE,
                                                quantity,
                                                discount_rate
                                            FROM   (SELECT id AS purchase_id
                                                    FROM   (SELECT order_id AS id
                                                            FROM   pharmacy_ordertracking po
                                                            WHERE  order_status = {0}
                                                                AND created_at > current_date - interval
                                                                                    '180'
                                                                                                day) AS
                                                        data
                                                        left join pharmacy_purchase USING(id)) AS
                                                purchase_data
                                                left join pharmacy_stockiolog USING(purchase_id)) AS data
                                    GROUP  BY stock_id,
                                            order_date) AS stock_io_info
                                left join pharmacy_stock USING(id)
                            WHERE  organization_id = {1}
                            ORDER  BY order_date DESC,
                                    number_of_order DESC,
                                    quantity DESC,
                                    product_full_name '''

            queryset_template = queryset_template.format(
                OrderTrackingStatus.COMPLETED, self.request.user.organization_id
            )
        data = Stock.objects.raw(queryset_template)
        return list(data)


class DateAndStatusWiseOrderAmount(generics.ListAPIView):
    """
        Report to show distributor order amount
        for given date range
    """
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = DateAndStatusWiseOrderAmountSerializer
    filterset_class = DateAndStatusWiseOrderAmountListFilter

    def get_queryset(self):
        filters = {
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER,
            "distributor": self.request.user.organization_id,
        }
        orders = Purchase.objects.filter(**filters).order_by('-purchase_date')
        orders = orders.extra(
            select={
                'purchase_date': "date(purchase_date AT TIME ZONE '{0}')".format(
                    timezone.get_current_timezone()),
            }
        ).values(
            "purchase_date",
            "tentative_delivery_date",
            "current_order_status",
        ).annotate(
            number_of_orders=Count('id'),
            amount_total=Sum(F('amount')),
            discount_total=Sum(F('discount') - F('round_discount')),
            grand_total=Sum(F('grand_total')),
        )
        return orders


class ResponsibleEmployeeWiseDeliverySheetList(generics.ListAPIView):
    """
        Report to show distributor order delivery sheet
        for given filters
    """
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ResponsibleEmployeeWiseDeliverySheetSerializer
    filterset_class = DistributorOrderListFilter

    def get_queryset(self):
        orders = self.request.user.organization.get_orders_for_distributor().order_by()
        orders = orders.values(
            'organization',
            'organization__alias',
            'organization__name',
            'organization__primary_mobile',
            'organization__address'
        ).annotate(
            unique_item=Count(Case(When(
                stock_io_logs__status=Status.DISTRIBUTOR_ORDER,
                then=F('stock_io_logs__stock'))), distinct=True),
            total_item=Coalesce(Sum(Case(When(
                stock_io_logs__status=Status.DISTRIBUTOR_ORDER,
                then=F('stock_io_logs__quantity')))), 0.00),
            order_ids=ArrayAgg(Cast('pk', IntegerField()), distinct=True),
            order_count=ArrayLength('order_ids'),
            order_amounts=JSONBAgg(
                Func(
                    Value('id'), 'id',
                    Value('grand_total'), 'grand_total',
                    Value('invoice_group'), 'invoice_group_id',
                    function='jsonb_build_object'
                ),
                ordering='pk',
            )
        )
        return orders

class ProductWiseStockTransferReport(generics.ListAPIView):
    """
        Report to show date, store_point, product wise transfer data
    """
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProductWiseStockTransferReportSerializer
    filterset_class = ProductWiseStockTransferReportFilter

    def get_queryset(self):
        queryset = StockIOLog().get_active_from_organization(
            self.request.user.organization_id
        ).filter(
            type=StockIOType.INPUT,
            transfer__organization=self.request.user.organization_id,
            transfer__status=Status.ACTIVE,
        ).order_by('-transfer__date')
        queryset = queryset.values(
            'transfer__date',
            'transfer__transfer_from',
            'transfer__transfer_from__alias',
            'transfer__transfer_from__name',
            'transfer__transfer_to',
            'transfer__transfer_to__alias',
            'transfer__transfer_to__name',
            'stock__product',
            'stock__product__name',
            'stock__product__alias',
            'stock__product__strength',
            'stock__product__trading_price',
            'stock__product__form__name',
            'stock__product__generic__name',
            'stock__product__manufacturing_company__name',
            'stock__product__subgroup__name',
            'stock__product__subgroup__product_group__type',
            'stock__product__subgroup__product_group__name',
        ).annotate(
            product_quantity=Sum(F('quantity')),
            unit_name=Case(
                When(
                    secondary_unit_flag=True,
                    then=F('secondary_unit__name'),
                    ),
                default=F('primary_unit__name'),
            ),
        )
        return queryset


class MismatchedStockWithIOProductList(generics.ListAPIView):
    """
        Report to show product list of mismatched stock with io
    """
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = MismatchedStockWithIOSerializer.List
    filterset_class = MismatchedStockWithIOProductListFilter

    def get_queryset(self):
        io_query_in = ((Q(stocks_io__purchase__isnull=True)
                        | Q(stocks_io__purchase__purchase_type=PurchaseType.PURCHASE))
                       & Q(stocks_io__status=Status.ACTIVE)
                       & Q(stocks_io__type=StockIOType.INPUT))
        io_query_out = ((Q(stocks_io__purchase__isnull=True)
                         | Q(stocks_io__purchase__purchase_type=PurchaseType.PURCHASE))
                        & Q(stocks_io__status=Status.ACTIVE)
                        & Q(stocks_io__type=StockIOType.OUT))
        queryset = Stock.objects.filter(
            status=Status.ACTIVE,
            store_point__status=Status.ACTIVE,
        ).prefetch_related('stocks_io').annotate(
            current_stock=Coalesce(Sum(Case(When(
                io_query_in, then=F('stocks_io__quantity')))), 0.00) -
            Coalesce(Sum(Case(When(
                io_query_out, then=F('stocks_io__quantity')))), 0.00)
        ).filter(~Q(stock=F('current_stock')))
        return queryset.order_by('-pk')
