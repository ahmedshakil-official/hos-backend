import re
import os

from django.db.models import Case, When, Subquery, F, CharField, BooleanField, Q, Max
from django.forms import TextInput
from django_filters import DateFilter
from django_filters.rest_framework import (
    CharFilter,
    FilterSet,
    DateFromToRangeFilter,
    DateTimeFromToRangeFilter,
    NumberFilter,
    BooleanFilter,
    RangeFilter,
)

from common.filters import CustomDateRangeFilterWidget
from common.utils import not_blank
from core.enums import AllowOrderFrom
from core.models import PersonOrganization, OrganizationSetting
from .models import (
    StockIOLog, StockAdjustment, Sales, Purchase,
    StockTransfer, Stock, ProductChangesLogs, OrderTracking,
    Product, DamageProduct
)
from .utils import filter_list_of_items, get_fields_where_value_is_not_null, get_delayed_orders


class StockReportFilter(FilterSet):
    """
    A filter class for filtering stocks

    Filter class should be used to filter stocks by store_point, group, generic and company.
    """
    store_point = CharFilter(field_name="stock__store_point__alias")
    product = CharFilter(field_name="stock__product__name")
    group = CharFilter(field_name="stock__product__subgroup__product_group__alias")
    generic = CharFilter(field_name="stock__product__generic__alias")
    company = CharFilter(field_name="stock__product__manufacturing_company__alias")
    expire_date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="expire_date")
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="date")
    # batch = BooleanFilter()

    class Meta:
        model = StockIOLog
        fields = ['store_point', 'product', 'group', 'generic', 'company', 'expire_date', 'date']


class StockDisbursementFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="date")
    store_point = CharFilter(field_name="store_point__alias")
    class Meta:
        model = StockAdjustment
        fields = ['store_point']


class PurchaseRequisitionFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="purchase_date")
    store_point = CharFilter(field_name="store_point__alias")
    department = CharFilter(field_name="department__alias")
    person = CharFilter(field_name="person_organization_receiver__alias")
    supplier = CharFilter(
        field_name="person_organization_supplier__alias",
        method="filter_suppliers"
    )

    def filter_suppliers(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = Purchase
        fields = []


class StockTransferRequisitionFilter(FilterSet):
    """
    Filter class for filtering stock transfer requisition by date range, employee, transfer_from, transfer_to.
    """
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="date")
    store_point = CharFilter(field_name="transfer_from__alias")
    store_point2 = CharFilter(field_name="transfer_to__alias")
    person = CharFilter(field_name="person_organization_by__alias")

    class Meta:
        model = StockTransfer
        fields = []


class StockTransferFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="date")
    store_point1 = CharFilter(field_name="transfer_from__alias")
    store_point2 = CharFilter(field_name="transfer_to__alias")

    class Meta:
        model = StockTransfer
        fields = []


class SalesFilter(FilterSet):
    date = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD H:M:S'}),
        field_name="sale_date")
    store_point = CharFilter(field_name="store_point__alias")

    class Meta:
        model = Sales
        fields = ['date', 'store_point', 'sales_mode']


class PurchaseListFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="purchase_date")
    store_point = CharFilter(field_name="store_point__alias")

    class Meta:
        model = Purchase
        fields = ['date', 'store_point']


class PurchaseOrderListFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="purchase_date")
    store_point = CharFilter(field_name="store_point__alias")

    class Meta:
        model = Purchase
        fields = ['date', 'store_point']


class StockAdjustmentFilter(FilterSet):
    """
    Filter class for filtering stock adjustment by date range, employee, storepoint and type.
    """
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="date")
    store_point = CharFilter(field_name="store_point__alias")
    person = CharFilter(field_name="person_organization_employee__alias")
    type = NumberFilter(field_name='stock_io_logs__type')

    class Meta:
        model = StockAdjustment
        fields = ['date', 'store_point', 'person']



class PurchaseSummaryFilter(FilterSet):
    store_point = CharFilter(
        field_name="store_point__alias",
        method='filter_store_point'
    )
    person = CharFilter(
        field_name="person_organization_supplier__alias",
        method='filter_supplier'
    )
    date = DateFromToRangeFilter(
        field_name="purchase_date",
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
    )

    class Meta:
        model = Purchase
        fields = ['date', 'store_point', 'person']

    def filter_store_point(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_supplier(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)


# class SalesPurchaseStockValueGroupWiseSummaryFilter(FilterSet):
#     store_point = CharFilter(
#         field_name="store_point__alias",
#         method='filter_store_point'
#     )
#     # person = CharFilter(
#     #     field_name="person_organization_supplier__alias",
#     #     method='filter_supplier'
#     # )
#     sale_date = DateFromToRangeFilter(
#         field_name="purchase__purchase_date",
#         widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
#     )
#     purchase_date = DateTimeFromToRangeFilter(
#         widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD H:M:S'}),
#         field_name="sales__sale_date")

#     class Meta:
#         model = Purchase
#         fields = ['date', 'store_point', 'person']

#     def filter_store_point(self, queryset, name, value):
#         return filter_list_of_items(queryset, name, value)


class DateAndStatusWiseOrderAmountListFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="purchase_date")
    delivery_date = DateFromToRangeFilter(
        widget= CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="tentative_delivery_date"
    )

    class Meta:
        model = Purchase
        fields = ['date', 'delivery_date' ]


class DistributorOrderListFilter(FilterSet):
    date = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD H:M:S'}),
        field_name="purchase_date")
    tentative_delivery_date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="tentative_delivery_date")
    current_order_status = CharFilter(
        field_name='current_order_status', method='filter_current_order_status')
    delivery_thana = CharFilter(
        field_name='organization__delivery_thana', method='filter_delivery_thana')
    delivery_hub = CharFilter(
        field_name='distributor__delivery_hub__alias', method='filter_delivery_hub')
    organization = CharFilter(
        field_name='organization__alias', method='filter_organization')
    order_rating = RangeFilter(
        field_name='order_rating',
        label='Order Rating Range',
        lookup_expr='range',
    )
    person_organizations = CharFilter(
        field_name='organization__entry_by__alias', method='filter_organization_added_by')
    responsible_employee = CharFilter(
        field_name='responsible_employee__alias', method='filter_responsible_employee')
    is_queueing_order = BooleanFilter(field_name="is_queueing_order")
    non_group_order = BooleanFilter(field_name="invoice_group", lookup_expr="isnull")
    is_delayed_order = BooleanFilter(field_name="is_delayed")
    area_code = CharFilter(
        field_name="organization__area__code",
        label="Area Code",
        method="filter_area_code"
    )

    def filter_current_order_status(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_delivery_thana(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_delivery_hub(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_organization(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_responsible_employee(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_organization_added_by(self, queryset, name, value):
        try:
            person_organizations = filter(not_blank(), value.split(','))
            persons = PersonOrganization.objects.values_list(
                'person__alias', flat=True
            ).filter(alias__in=person_organizations)
            values = ','.join(map(str, list(persons)))
        except:
            values = ""
        return filter_list_of_items(queryset, name, values)

    def filter_area_code(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = Purchase
        fields = [
            'date',
            'current_order_status',
            'delivery_thana',
            'delivery_hub',
            'organization',
            'order_rating',
            'responsible_employee',
            'person_organizations',
            'tentative_delivery_date',
            'is_queueing_order',
            'is_delayed_order',
            "area_code",
        ]

class DistributorOrderProductSummaryFilter(FilterSet):
    date = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD H:M:S'}),
        field_name="purchase_date")
    tentative_delivery_date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="tentative_delivery_date")
    responsible_employee = CharFilter(
        field_name='responsible_employee__alias', method='filter_responsible_employee')
    delivery_thana = CharFilter(
        field_name='organization__delivery_thana', method='filter_delivery_thana')
    delivery_hub = CharFilter(
        field_name='distributor__delivery_hub__alias', method='filter_delivery_hub')
    is_queueing_order = BooleanFilter(field_name="is_queueing_order")

    def filter_responsible_employee(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_delivery_thana(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_delivery_hub(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = Purchase
        fields = [
            'date',
            'responsible_employee',
            'tentative_delivery_date',
            'is_queueing_order',
            'delivery_hub',
        ]

class DistributorOrderProductSummaryIOFilter(FilterSet):
    date = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD H:M:S'}),
        field_name="purchase__purchase_date")
    tentative_delivery_date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="purchase__tentative_delivery_date")
    responsible_employee = CharFilter(
        field_name='purchase__responsible_employee__alias', method='filter_responsible_employee')
    delivery_thana = CharFilter(
        field_name='purchase__organization__delivery_thana', method='filter_delivery_thana')
    delivery_hub = CharFilter(
        field_name='purchase__distributor__delivery_hub__alias', method='filter_delivery_hub')
    is_queueing_order = BooleanFilter(field_name="purchase__is_queueing_order")

    def filter_responsible_employee(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_delivery_thana(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_delivery_hub(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = StockIOLog
        fields = [
            'date',
            'responsible_employee',
            'tentative_delivery_date',
            'is_queueing_order',
            'delivery_hub',
        ]


class DistributorSalesAbleStockProductListFilter(FilterSet):
    """
    A filter class for filtering stocks

    Filter class should be used to filter stocks by company.
    """
    manufacturing_company = CharFilter(
        field_name="product__manufacturing_company__alias", method='filter_multiple')
    unit_type = CharFilter(
        field_name="product__unit_type")
    generic = CharFilter(
        field_name="product__generic__alias", method='filter_multiple')
    availability = CharFilter(method='filter_availability')
    product_group = CharFilter(
        field_name="product__subgroup__product_group__alias",
        method="filter_multiple",
    )

    def filter_availability(self, queryset, name, value):
        values = re.split(r',\s*', value)

        # Get Organization Setting
        distributor_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
        default_org_setting = OrganizationSetting.objects.filter(
            organization__id=distributor_id
        ).only('overwrite_order_mode_by_product', 'allow_order_from')
        overwrite_order_mode_by_product = default_org_setting.values_list(
            'overwrite_order_mode_by_product', flat=True
        )
        allow_order_from = default_org_setting.values_list(
            'allow_order_from', flat=True
        )
        queryset = queryset.filter(
            is_salesable=True
        ).annotate(
            org_order_mode=Subquery(
                overwrite_order_mode_by_product[:1],
                output_field=BooleanField()
            ),
            org_allow_order_from=Subquery(
                allow_order_from[:1],
                output_field=CharField()
            ),
            order_mode=Case(
                When(
                    org_order_mode=True,
                    then=F('product__order_mode')
                ),
                default=F('org_allow_order_from'),
                output_field=CharField()
            )
        ).exclude(
            Q(orderable_stock__lte=0) & Q(order_mode=AllowOrderFrom.STOCK)
        )
        if 'PRE_ORDER' in values and 'IN_STOCK' in values:
            return queryset
        elif 'IN_STOCK' in values:
            return queryset.filter(
                product__is_queueing_item=False,
            )
        elif 'PRE_ORDER' in values:
            return queryset.filter(
                product__is_queueing_item=True,
            )
        return queryset

    def filter_multiple(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = Stock
        fields = [
            'manufacturing_company',
            'unit_type',
            'generic',
            'availability',
        ]


class ProductWiseStockTransferReportFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="transfer__date")
    store_point = CharFilter(
        field_name="transfer__transfer_from__alias", method='filter_transfer_from')
    store_point2 = CharFilter(
        field_name="transfer__transfer_to__alias", method='filter_transfer_to')
    company = CharFilter(
        field_name="stock__product__manufacturing_company__alias",
        method='filter_manufacturing_company'
    )
    product_group = CharFilter(
        field_name="stock__product__subgroup__product_group__alias",
        method='filter_product_group'
    )

    def filter_manufacturing_company(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_transfer_from(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_transfer_to(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_product_group(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = StockIOLog
        fields = [
            'date',
            'store_point',
            'store_point2',
            'company',
            'product_group',
        ]


class MismatchedStockWithIOProductListFilter(FilterSet):
    """
    A filter class for filtering stocks

    Filter class should be used to filter stocks by organization.
    """
    organization = CharFilter(
        field_name="organization__alias", method='filter_organization')

    def filter_organization(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = Stock
        fields = ['organization']


class ProductChangesLogsFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="date")
    fields = CharFilter(method='filter_fields')

    def filter_fields(self, queryset, name, value):
        fields = [
            'name',
            'strength',
            'generic',
            'form',
            'manufacturing_company',
            'trading_price',
            'purchase_price',
            'order_limit_per_day',
            'is_published',
            'discount_rate',
            'order_mode',
            'is_flash_item',
            'unit_type',
            'compartment',
            'is_queueing_item',
        ]
        return get_fields_where_value_is_not_null(queryset, fields, value)

    class Meta:
        model = ProductChangesLogs
        fields = ['date']


class OrderStatusChangeLogFilter(FilterSet):
    delivery_date = DateFilter(
        field_name="order__invoice_group__delivery_date",
        widget=TextInput(attrs={'placeholder': 'YYYY-MM-DD'})
    )
    invoice_group = CharFilter(
        field_name="order__invoice_group__alias",
    )
    responsible_employee = CharFilter(
        field_name='order__invoice_group__responsible_employee__alias', method='filter_responsible_employee')

    current_status_only = BooleanFilter(
        method='filter_current_status_only'
    )

    def filter_current_status_only(self, queryset, name, value):
        if value:
            queryset = queryset.values(
                'order'
            ).annotate(
                max_date=Max('date'),
                max_id=Max('id')
            ).order_by(
                'order'
            )

            new_queryset = OrderTracking.objects.none()
            for item in queryset:
                new_queryset |= OrderTracking.objects.filter(
                    order=item['order'],
                    date=item['max_date']
                )
            new_queryset = new_queryset.distinct('order__invoice_group', 'status')
            return new_queryset

        return queryset

    def filter_responsible_employee(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = OrderTracking
        fields = [
            'delivery_date',
            'invoice_group',
            'responsible_employee',
        ]

class ProductFilter(FilterSet):
    stock_ids = CharFilter(
        field_name="stock_list__id",
        method="filter_multiple"
    )
    manufacturing_company = CharFilter(
        field_name="manufacturing_company__alias",
        method="filter_multiple"
    )


    def filter_multiple(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = Product
        fields = [
            "stock_ids",
            "manufacturing_company",
        ]

class DamageItemFilter(FilterSet):
    type = CharFilter(
        field_name="type",
    )

    class Meta:
        model = DamageProduct
        fields = [
            "type"
        ]