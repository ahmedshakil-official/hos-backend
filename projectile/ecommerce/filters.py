from django.db.models import Q
from django_filters.rest_framework import (
    CharFilter,
    FilterSet,
    DateFromToRangeFilter,
    DateTimeFromToRangeFilter,
    NumberFilter,
    BooleanFilter,
    DateFilter,
    RangeFilter,
)
from django_filters import RangeFilter as RNGFilter
from common.filters import CustomDateRangeFilterWidget
from common.utils import not_blank
from core.models import PersonOrganization
from pharmacy.utils import filter_list_of_items
from .models import (
    OrderInvoiceGroup,
    ShortReturnItem,
    InvoiceGroupDeliverySheet,
    ShortReturnLog,
    DeliverySheetInvoiceGroup,
    TopSheetSubTopSheet,
    InvoiceGroupPdf,
    InvoicePdfGroup,
)

class OrderInvoiceGroupListFilter(FilterSet):
    date = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD H:M:S'}),
        field_name="date")
    tentative_delivery_date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="delivery_date")
    delivery_date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="delivery_date")
    current_order_status = CharFilter(
        field_name='current_order_status', method='filter_current_order_status')
    delivery_thana = CharFilter(
        field_name='order_by_organization__delivery_thana', method='filter_delivery_thana')
    delivery_hub = CharFilter(
        field_name='order_by_organization__delivery_hub__alias', method='filter_delivery_hub')
    organization = CharFilter(
        field_name='order_by_organization__alias', method='filter_organization')
    person_organizations = CharFilter(
        field_name='order_by_organization__entry_by__alias', method='filter_organization_added_by')
    responsible_employee = CharFilter(
        field_name='responsible_employee__alias', method='filter_responsible_employee')
    # is_queueing_order = BooleanFilter(field_name="is_queueing_order")
    customer_rating = RangeFilter(
        field_name='customer_rating',
        label='Customer Rating Range',
        lookup_expr='range',
    )
    # Custom boolean filter field to filter by whether an OrderInvoiceGroup has a related DeliverySheetInvoiceGroup
    has_no_delivery_sheet = BooleanFilter(
        method="filter_has_no_delivery_sheet",
        label='Has No Delivery Sheet',
    )

    area_code = CharFilter(
        field_name="order_by_organization__area__code",
        label="Area Code",
        method="filter_area_code"
    )
    id_range = RangeFilter(
        field_name='id',
        label='ID Range',
        lookup_expr='range',
    )

    def filter_has_no_delivery_sheet(self, queryset, name, value):
        if value:
            # Filter OrderInvoiceGroups that do not have a related DeliverySheetInvoiceGroup
            return queryset.filter(delivery_sheet_invoice_groups__isnull=True)
        else:
            # Filter OrderInvoiceGroups that have a related DeliverySheetInvoiceGroup
            return queryset.filter(delivery_sheet_invoice_groups__isnull=False)

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
        model = OrderInvoiceGroup
        fields = [
            # 'date',
            'current_order_status',
            'delivery_thana',
            'delivery_hub',
            'organization',
            'responsible_employee',
            'person_organizations',
            'tentative_delivery_date',
            'delivery_date',
            # 'is_queueing_order',
            'customer_rating',
            'has_no_delivery_sheet',
            "area_code",
            "id_range",
        ]


class ShortReturnItemFilter(FilterSet):
    date = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="short_return_log__date")
    invoice_group = CharFilter(
        field_name='short_return_log__invoice_group__alias',
    )
    invoice_group_id = CharFilter(
        field_name='short_return_log__invoice_group__id',
    )
    order = CharFilter(
        field_name='short_return_log__order__alias',
    )
    short_return_type = CharFilter(field_name="type")
    responsible_employee = CharFilter(
        field_name='short_return_log__order__responsible_employee__alias', method='filter_multiple')
    product = CharFilter(
        field_name='stock__product__alias', method='filter_multiple')
    status = CharFilter(
        field_name='status',
        method='filter_multiple'
    )
    organization = CharFilter(
        field_name='short_return_log__order_by_organization__alias',
        method='filter_multiple'
    )
    delivery_hub = CharFilter(
        field_name='short_return_log__order_by_organization__delivery_hub__alias',
        method='filter_multiple'
    )
    delivery_date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={"placeholder": "YYYY-MM-DD"}),
        field_name='short_return_log__invoice_group__delivery_date',
    )
    approved_at = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={"placeholder": "YYYY-MM-DD HH:MM:SS"}),
        field_name='short_return_log__approved_at',
    )
    responsible_employee = CharFilter(
        field_name='short_return_log__invoice_group__responsible_employee__alias',
        method='filter_multiple'
    )

    def filter_multiple(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = ShortReturnItem
        fields = [
            'date',
            'invoice_group',
            'invoice_group_id',
            'order',
            'short_return_type',
            'responsible_employee',
            'product',
            'status',
            'organization',
            'delivery_hub',
            'responsible_employee',
        ]


class InvoiceGroupDeliverySheetListFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="date")
    responsible_employee = CharFilter(
        field_name='responsible_employee__alias', method='filter_responsible_employee')
    employee_code = CharFilter(
        field_name='responsible_employee__code',
    )
    invoice_group = CharFilter(
        field_name='delivery_sheet_items__delivery_sheet_invoice_groups__invoice_group__alias',
        method='filter_multiple'
    )
    type = CharFilter(
        field_name="type",
    )
    top_sheet = CharFilter(
        field_name='top_sheet',
        method='filter_by_top_sheet'
    )
    sub_top_sheet = CharFilter(
        field_name='sub_top_sheet',
        method='filter_by_sub_top_sheet'
    )
    keyword = CharFilter(
        field_name="keyword",
        method="filter_by_keyword",
    )

    def filter_by_keyword(self, queryset, name, value):
        if value and value.isdigit():
            sub_sheet_ids = TopSheetSubTopSheet().get_all_actives().filter(
                top_sheet__id=value,
            ).values_list("sub_top_sheet__id", flat=True)
        elif value:
            sub_sheet_ids = TopSheetSubTopSheet().get_all_actives().filter(
                top_sheet__name__icontains=value,
            ).values_list("sub_top_sheet__id", flat=True)

        return queryset.filter(id__in=sub_sheet_ids)

    def filter_by_top_sheet(self, queryset, name, value):
        top_sheet_list = value.split(',')
        sub_sheet_ids = TopSheetSubTopSheet().get_all_actives().filter(
            top_sheet__alias__in=top_sheet_list
        ).values_list("sub_top_sheet__id", flat=True)

        return queryset.filter(id__in=sub_sheet_ids)

    def filter_by_sub_top_sheet(self, queryset, name, value):
        sub_sheet_list = value.split(',')
        top_sheet = TopSheetSubTopSheet().get_all_actives().filter(
            sub_top_sheet__alias__in=sub_sheet_list,
        ).values_list("top_sheet__id", flat=True)

        return queryset.filter(id__in=top_sheet)

    def filter_responsible_employee(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_multiple(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)


    class Meta:
        model = InvoiceGroupDeliverySheet
        fields = [
            'date',
            'responsible_employee',
            'employee_code',
            'type',
            'top_sheet',
            'sub_top_sheet',
        ]


class ShortReturnLogListFilter(FilterSet):
    date = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="date")
    type = NumberFilter(field_name="type")
    received_by = CharFilter(field_name="received_by__alias")
    approved_by = CharFilter(field_name="approved_by__alias")
    invoice_group = CharFilter(field_name="invoice_group__alias")
    delivery_date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={"placeholder": "YYYY-MM-DD"}),
        field_name='invoice_group__delivery_date',
    )
    approved_at = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={"placeholder": "YYYY-MM-DD HH:MM:SS"}),
        field_name='approved_at',
    )
    responsible_employee = CharFilter(
        field_name='invoice_group__responsible_employee__alias',
        method='filter_multiple'
    )

    def filter_multiple(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = ShortReturnLog
        fields = [
            'date',
            'type',
            'received_by',
            'approved_by',
            'invoice_group',
        ]


class ShortReturnLogListWithoutTypeFilter(FilterSet):
    date = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={"placeholder": "YYYY-MM-DD"}),
        field_name="date")
    received_by = CharFilter(field_name="received_by__alias", method="filter_multiple")
    approved_by = CharFilter(field_name="approved_by__alias", method="filter_multiple")
    invoice_group = CharFilter(field_name="invoice_group__alias", method="filter_multiple")
    delivery_date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={"placeholder": "YYYY-MM-DD"}),
        field_name='invoice_group__delivery_date'
    )
    approved_at = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={"placeholder": "YYYY-MM-DD HH:MM:SS"}),
        field_name='approved_at',
    )
    status = CharFilter(
        field_name='status',
        method='filter_multiple'
    )
    responsible_employee = CharFilter(
        field_name='invoice_group__responsible_employee__alias',
        method='filter_multiple'
    )
    delivery_hub = CharFilter(
        field_name='order_by_organization__delivery_hub__alias',
        method='filter_multiple'
    )


    def filter_multiple(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = ShortReturnLog
        fields = [
            'date',
            'received_by',
            'approved_by',
            'invoice_group',
            'delivery_hub',
        ]


class DeliverySheetInvoiceGroupReportFilter(FilterSet):
    date = DateFilter(field_name="delivery_sheet_item__invoice_group_delivery_sheet__date")

    class Meta:
        model = DeliverySheetInvoiceGroup
        fields = [
            'date',
        ]

def assigned_unassigned_filter(query_params):
    filter_conditions = []

    # Organization filtering
    keyword = query_params.get("keyword")

    if keyword:
        filter_conditions.append(
            Q(order_by_organization__name__icontains=keyword)|
            Q(order_by_organization__primary_mobile__icontains=keyword)
        )

    # List of organizations filtering
    organization_alias = query_params.get("organizations", None)
    if organization_alias:
        organization_alias = [alias for alias in organization_alias.split(",")]
        filter_conditions.append(Q(order_by_organization__alias__in=organization_alias))

    # List of responsible employees filtering
    responsible_employee_alias = query_params.get("responsible_employees", None)
    if responsible_employee_alias:
        responsible_employee_alias = [alias for alias in responsible_employee_alias.split(",")]
        filter_conditions.append(Q(invoice_group_delivery_sheet__responsible_employee__alias__in=responsible_employee_alias))

    return filter_conditions

class InvoiceGroupPdfListFilter(FilterSet):
    invoice_id_range = RangeFilter(
        field_name='invoice_group__id',
        label='ID Range',
        lookup_expr='range',
    )

    class Meta:
        model = InvoiceGroupPdf
        fields = ["invoice_id_range"]


class InvoicePdfGroupListFilter(FilterSet):
    date = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD H:M:S'}),
        field_name="created_at"
    )
    tentative_delivery_date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="delivery_date"
    )
    delivery_date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="delivery_date"
    )
    area = CharFilter(
        field_name="area__code",
        label="Area Code",
        method="filter_area_code"
    )

    def filter_area_code(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = InvoicePdfGroup
        fields = [
            "date",
            "tentative_delivery_date",
            "delivery_date",
            "area",
        ]
