from django_filters.rest_framework import (
    CharFilter,
    FilterSet,
    DateFromToRangeFilter,
    DateTimeFromToRangeFilter,
    NumberFilter,
    BooleanFilter,
)
from common.filters import CustomDateRangeFilterWidget
from common.utils import not_blank
from pharmacy.utils import filter_list_of_items
from .models import (
    PurchasePrediction,
    Procure,
    ProcureItem,
    ProcureIssueLog,
    ProcureGroup,
    ProcureReturn,
    ProcurePayment,
)


class PurchasePredictionListFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="date")


    class Meta:
        model = PurchasePrediction
        fields = [
            'date',
        ]


class ProcureListFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="date")
    employee = CharFilter(
        field_name='employee__alias', method='filter_multiple')
    supplier = CharFilter(
        field_name='supplier__alias', method='filter_multiple')
    contractor = CharFilter(
        field_name='contractor__alias', method='filter_multiple')
    current_status = CharFilter(
        field_name='current_status', method='filter_multiple')
    aliases = CharFilter(
        field_name="alias", method="filter_multiple")
    is_credit_purchase = CharFilter(
        field_name="is_credit_purchase", method="filter_is_credit_purchase")
    procure_group = CharFilter(
        field_name="procure_group__alias", method="filter_procure_group")
    has_open_credit = BooleanFilter(
        label="Has open credit", method="filter_has_open_credit")

    def filter_multiple(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_is_credit_purchase(self, queryset, name, value):
        is_credit_purchase = value.lower() == "true"
        return queryset.filter(is_credit_purchase=is_credit_purchase)

    def filter_procure_group(self, queryset, name, value):
        """
        If procure_group__alias exist and open_credit_balance is greater than zero then
        it will return procures under the procure group.
        """
        return queryset.filter(procure_group__alias=value, open_credit_balance__gt=0)

    def filter_has_open_credit(self, queryset, name, value):
        """
        Returns:  All procures where open_credit_balance is greater than zero.
        """
        if value:
            return queryset.filter(open_credit_balance__gt=0.00)
        return queryset



    class Meta:
        model = Procure
        fields = [
            'date',
            'employee',
            'supplier',
            'current_status',
            "aliases",
            "is_credit_purchase",
            "procure_group",
            "has_open_credit",
        ]


class ProcurementReportProductWiseFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="date")
    person_organizations = CharFilter(
        field_name='procure__employee__alias', method='filter_employee')
    person = CharFilter(
        field_name='procure__supplier__alias', method='filter_supplier')
    supplier = CharFilter(
        field_name='procure__supplier__alias', method='filter_supplier')

    def filter_employee(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_supplier(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)


    class Meta:
        model = ProcureItem
        fields = [
            'date',
            'person_organizations',
            'person',
            'supplier',
        ]


class ProcurementIssueReportFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="prediction_item__date")
    person_organizations = CharFilter(
        field_name='employee__alias', method='filter_multiple')
    person = CharFilter(
        field_name='supplier__alias', method='filter_multiple')
    supplier = CharFilter(
        field_name='supplier__alias', method='filter_multiple')
    product = CharFilter(
        field_name='stock__product__alias', method='filter_multiple')

    def filter_multiple(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)


    class Meta:
        model = ProcureIssueLog
        fields = [
            'date',
            'person_organizations',
            'person',
            'product',
            'supplier',
        ]


class ProcureGroupListFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="date")
    supplier = CharFilter(
        field_name='supplier__alias', method='filter_multiple')
    contractor = CharFilter(
        field_name='procure_group_procures__contractor__alias', method='filter_multiple')
    has_open_credit = BooleanFilter(
        label="Has open credit", method="filter_has_open_credit")

    def filter_multiple(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_has_open_credit(self, queryset, name, value):
        """
        Returns:  All procures where open_credit_balance is greater than zero.
        """
        if value:
            return queryset.filter(open_credit_balance__gt=0.00)
        return queryset

    class Meta:
        model = ProcureGroup
        fields = [
            'date',
            'supplier',
            'current_status',
        ]


class ProcureItemPurchaseListFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={"placeholder": "YYYY-MM-DD"}),
        field_name="date",
    )
    product = CharFilter(
        field_name="stock__product__alias",
        method="filter_multiple"
    )
    contractor = CharFilter(
        field_name="procure__contractor__alias",
        method="filter_multiple"
    )

    def filter_multiple(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = ProcureItem
        fields = [
            "date",
            "product",
            "contractor",
        ]


class ProcureReturnListFilter(FilterSet):
    buyer = CharFilter(
        field_name="procure__employee__alias",
        method="filter_multiple"
    )
    contractor = CharFilter(
        field_name="contractor__alias",
        method="filter_multiple"
    )
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={"placeholder": "YYYY-MM-DD"}),
        field_name="date",
    )
    employee = CharFilter(
        field_name="employee__alias",
        method="filter_multiple"
    )
    full_settlement_date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={"placeholder": "YYYY-MM-DD"}),
        field_name="full_settlement_date",
    )
    purchase_date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={"placeholder": "YYYY-MM-DD"}),
        field_name="procure__date",
    )

    def filter_multiple(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = ProcureReturn
        fields = [
            "buyer",
            "contractor",
            "current_status",
            "date",
            "employee",
            "full_settlement_date",
            "purchase_date",
            "reason",
        ]


class ProcurePaymentFilter(FilterSet):
    procure = CharFilter(
        field_name="procure__alias"
    )

    class Meta:
        model = ProcurePayment
        fields = [
            "procure"
        ]


class ProcureInfoReportFilter(FilterSet):

    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD'}),
        field_name="date")
    supplier = CharFilter(
        field_name='supplier__alias', method='filter_multiple')
    contractor = CharFilter(
        field_name='procure_group_procures__contractor__alias', method='filter_multiple')
    has_open_credit = BooleanFilter(
        label="Has open credit", method="filter_has_open_credit")

    def filter_multiple(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    def filter_has_open_credit(self, queryset, name, value):
        """
        Returns:  All procures where open_credit_balance is greater than zero.
        """
        if value:
            return queryset.filter(open_credit_balance__gt=0.00)
        return queryset

    class Meta:
        model = ProcureGroup
        fields = [
            "date",
            "supplier",
            "credit_status",
            "current_status",
            "credit_payment_term_date",
        ]
