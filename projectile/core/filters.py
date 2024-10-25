from django.db.models import Q, F, Max
from django_filters.rest_framework import (
    CharFilter,
    FilterSet,
    DateFromToRangeFilter,
    DateTimeFromToRangeFilter,
)
from common.filters import CustomDateRangeFilterWidget
from ecommerce.models import OrderInvoiceGroup
from pharmacy.utils import filter_list_of_items
from .models import (
    Organization, PersonOrganization, Issue,
    EmployeeManager, ScriptFileStorage, PasswordReset
)


class IssueListFilter(FilterSet):
    date = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD H:M:S'}),
        field_name="date")
    current_issue_status = CharFilter(
        field_name='current_issue_status', method='filter_multiple')
    issue_type = CharFilter(
        field_name='type', method='filter_multiple')
    order = CharFilter(
        field_name='order__alias', method='filter_multiple')
    organization = CharFilter(
        field_name='issue_organization__alias', method='filter_multiple')
    reported_to = CharFilter(
        field_name='reported_to__alias', method='filter_multiple')
    reported_against = CharFilter(
        field_name='reported_against__alias', method='filter_multiple')
    responsible_to_resolve = CharFilter(
        field_name='responsible_to_resolve__alias', method='filter_multiple')
    entry_by = CharFilter(
        field_name='entry_by__alias', method='filter_multiple')

    def filter_multiple(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = Issue
        fields = [
            'date',
            'current_issue_status',
            'issue_type',
            'order',
            'organization',
            'reported_to',
            'reported_against',
            'responsible_to_resolve',
            'entry_by',
        ]


class PersonOrganizationEmployeeListFilter(FilterSet):
    code = CharFilter(
        field_name='code',
        method="filter_multiple"
    )
    designation = CharFilter(
        field_name='designation__alias',
        method='filter_multiple'
    )
    manager = CharFilter(
        field_name='managers__manager__alias',
        method='filter_multiple'
    )

    def filter_multiple(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = PersonOrganization
        fields = [
            'code',
            'designation',
            'manager',
        ]


# Organization List filter by (delivery thana, delivery sub area)
class OrganizationListFilter(FilterSet):
    status = CharFilter(field_name="status")
    created_at = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD H:M:S'}),
        field_name="created_at"
    )
    added_by = CharFilter(
        field_name='entry_by__alias'
    )
    min_order_amount = CharFilter(
        field_name='min_order_amount'
    )
    primary_responsible_person = CharFilter(
        field_name='primary_responsible_person__alias'
    )
    secondary_responsible_person = CharFilter(
        field_name='secondary_responsible_person__alias'
    )
    delivery_thana = CharFilter(
        field_name='delivery_thana'
    )
    delivery_sub_area = CharFilter(
        field_name='delivery_sub_area'
    )
    delivery_hub = CharFilter(
        field_name='delivery_hub__alias'
    )

    area_code = CharFilter(
        field_name="area__code",
        label="Area Code",
        method="filter_multiple"
    )

    def filter_multiple(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)

    class Meta:
        model = Organization
        fields = [
            'status',
            'created_at',
            'added_by',
            'delivery_thana',
            'delivery_sub_area',
            'delivery_hub',
            'min_order_amount',
            'primary_responsible_person',
            'secondary_responsible_person',
            "area_code",
        ]


class EmployeeManagerListFilter(FilterSet):
    employee = CharFilter(field_name="employee__alias")
    manager = CharFilter(field_name="manager__alias")
    status = CharFilter(field_name="status")

    class Meta:
        model = EmployeeManager
        fields = ['employee', 'manager', 'status']


class PossibleResponsiblePersonForOrganization(FilterSet):
    primary_responsible_person = CharFilter(field_name="primary_responsible_person__alias")
    mismatch_only = CharFilter(method='primary_responsible_person_mismatch')

    def primary_responsible_person_mismatch(self, queryset, name, value):
        if value == 'true' or value == 'True' or value == 'TRUE':
            import datetime

            from ecommerce.models import OrderInvoiceGroup
            from common.enums import Status
            from pharmacy.enums import OrderTrackingStatus

            new_queryset = Organization.objects.none()
            invoice_groups = OrderInvoiceGroup.objects.filter(
                status=Status.ACTIVE,
                # delivery_date__lt=datetime.date.today(),
                responsible_employee__isnull=False
            ).select_related('order_by_organization').values(
                'delivery_date',
                'responsible_employee',
                'order_by_organization'
            ).exclude(
                current_order_status__in=[
                    OrderTrackingStatus.REJECTED,
                    OrderTrackingStatus.CANCELLED
                ]
            ).order_by('-delivery_date').distinct('delivery_date', 'order_by_organization')
            """
            Get Invoices order by Organization
            {
                630: [
                        {'delivery_date': 2022, 11, 20, 'responsible_employee': 102423},
                        {'delivery_date': 2022, 11, 19, 'responsible_employee': 102423},
                        {'delivery_date': 2022, 11, 18, 'responsible_employee': 102423},
                        {'delivery_date': 2022, 11, 17, 'responsible_employee': 102423}
                    ]
                303: [
                        {'delivery_date': 2022, 11, 15, 'responsible_employee': 102472},
                        {'delivery_date': 2021, 11, 9, 'responsible_employee': 100043}
                    ],
            }
            """
            invoices_group_by_organization = {}
            for invoice_group in invoice_groups:
                organization_id = invoice_group['order_by_organization']
                if organization_id not in invoices_group_by_organization:
                    invoices_group_by_organization[organization_id] = []
                invoices_group_by_organization[organization_id].append(invoice_group)
            """
            Get only those responsible employee where they have equal or more than 3 invoices assigned to them
            {
                630: [
                    {'delivery_date': 2022, 11, 20, 'responsible_employee': 102423},
                    {'delivery_date': 2022, 11, 19, 'responsible_employee': 102423},
                    {'delivery_date': 2022, 11, 18, 'responsible_employee': 102423},
                ]
            }
            """
            invoices_minimum_three_deliveries = {}
            for organization in invoices_group_by_organization:
                if len(invoices_group_by_organization[organization]) >= 3:
                    invoices_minimum_three_deliveries[organization] = invoices_group_by_organization[organization]
                else:
                    invoices_minimum_three_deliveries[organization] = None
            """
            Get Only those responsible employee where they did 3 deliveries consecutively.
            {
                630: <PersonOrganization: 90151 - 2235>,
            }
            """
            invoices_res_emp_by_org = {}
            for organization in invoices_minimum_three_deliveries:
                invoices_res_emp_by_org[organization] = None
                if invoices_minimum_three_deliveries[organization] is not None:
                    employees = []
                    for invoice_group in invoices_minimum_three_deliveries[organization]:
                        employees.append(invoice_group['responsible_employee'])
                    responsible_employee_id = []
                    if len(employees) > 0:
                        # Check if the employee is responsible for 3 consecutive deliveries
                        for index in range(len(employees) - 2):
                            if employees[index] == employees[index + 1] and employees[index + 1] == employees[index + 2]:
                                responsible_employee_id.append(employees[index])
                    if len(responsible_employee_id) > 0:
                        invoices_res_emp_by_org[organization] = PersonOrganization.objects.get(
                            pk=responsible_employee_id[0])
                    employees.clear()
                    responsible_employee_id.clear()

            for org in queryset:
                # If invoices_res_emp_by_org dict has the current organization in it, that means the organization has
                # three or more deliveries, then we will check primary responsible person mismatch
                if org.id in invoices_res_emp_by_org:
                    if invoices_res_emp_by_org[org.id] is not None:
                        if invoices_res_emp_by_org[org.id] != org.primary_responsible_person:
                            new_queryset |= Organization.objects.filter(id=org.id)
                else:
                    continue
                    # if org.primary_responsible_person is not None:
                    #     new_queryset |= Organization.objects.filter(id=org.id)
            return new_queryset
        return queryset

    class Meta:
        model = Organization
        fields = ['id', 'alias', 'primary_responsible_person', 'mismatch_only']


class ScriptFileListFilter(FilterSet):
    date = DateFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={'placeholder': 'YYYY-MM-DD '}),
        field_name="date")
    type = CharFilter(field_name="file_purpose")

    class Meta:
        model = ScriptFileStorage
        fields = [
            'date',
            'type'
        ]


class PasswordResetFilter(FilterSet):
    reset_status = CharFilter(field_name="reset_status")
    type = CharFilter(field_name="type")
    date = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={"placeholder": "YYYY-MM-DD H:M:S"}),
        field_name="created_at"
    )
    reset_date = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={"placeholder": "YYYY-MM-DD H:M:S"}),
        field_name="reset_date"
    )
    organization = CharFilter(method="filter_organization_by_aliases")

    def filter_organization_by_aliases(self, queryset, name, value):
        aliases = value.split(',')
        return queryset.filter(organization__alias__in=aliases)

    class Meta:
        model = PasswordReset
        fields = [
            "reset_status",
            "type",
            "date",
            "reset_date",
            "organization"
        ]


class OrderInvoiceGroupFilter(FilterSet):
    status = CharFilter(field_name="order_by_organization__status")
    created_at = DateTimeFromToRangeFilter(
        widget=CustomDateRangeFilterWidget(attrs={"placeholder": "YYYY-MM-DD H:M:S"}),
        field_name="order_by_organization__created_at"
    )
    added_by = CharFilter(
        field_name="order_by_organization__entry_by__alias"
    )
    min_order_amount = CharFilter(
        field_name="order_by_organization__min_order_amount"
    )
    primary_responsible_person = CharFilter(
        field_name="order_by_organization__primary_responsible_person__alias"
    )
    secondary_responsible_person = CharFilter(
        field_name="order_by_organization__secondary_responsible_person__alias"
    )
    delivery_thana = CharFilter(
        field_name="order_by_organization__delivery_thana"
    )
    delivery_sub_area = CharFilter(
        field_name="order_by_organization__delivery_sub_area"
    )
    delivery_hub = CharFilter(
        field_name="order_by_organization__delivery_hub__alias"
    )
    area_code = CharFilter(
        field_name="organization__area__code",
        label="Area Code",
        method="filter_area_code"
    )

    def filter_area_code(self, queryset, name, value):
        return filter_list_of_items(queryset, name, value)


    class Meta:
        model = OrderInvoiceGroup
        fields = [
            "status",
            "created_at",
            "added_by",
            "delivery_thana",
            "delivery_sub_area",
            "delivery_hub",
            "min_order_amount",
            "primary_responsible_person",
            "secondary_responsible_person",
            "area_code",
        ]
