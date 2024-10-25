from django.contrib import admin
from common.admin import (
    CreatedAtUpdatedAtBaseModelWithOrganizationAdmin,
    NameSlugDescriptionBaseOrganizationWiseModelAdmin,
)

from .models import (
    Accounts, AccountCheque,
    Transaction, TransactionHead,
    PayableToPerson, TransactionPurchase,
    PatientBill,
    BillTransaction,
    OrganizationWiseOmisService,
    OrganizationWiseOmisServiceBill,
    TransactionPayablePerson,
    SalesTransaction,
)


class AccountsAdmin(NameSlugDescriptionBaseOrganizationWiseModelAdmin):

    fieldsets = (
        ('Accounts', {
            'classes': ('wide',),
            'fields': ('organization', 'name', 'opening_balance', 'balance')}
        ),

        ('Bank Details', {
            'classes': ('wide',),
            'fields': ('type', 'bank', 'branch', 'ac_no')}
        ),
        ('Description', {
            'classes': ('wide',),
            'fields': ('description', )}
        ),

        ('Status', {
            'classes': ('wide',),
            'fields': ('entry_by', 'updated_by', 'status', )}
        ),
    )

    list_display = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_display + (
        'balance', 'type', 'bank',
        'branch', 'ac_no', 'alias',
    )
    list_filter = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_filter + ('type',)
    search_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.search_fields + (
        'type', 'alias'
    )
    raw_id_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.raw_id_fields

admin.site.register(Accounts, AccountsAdmin)


class AccountChequeAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):

    fieldsets = (
        ('Account Cheque Details', {
            'classes': ('wide',),
            'fields': ('account', 'reference_name', 'condition', )}
        ),

        ('Status', {
            'classes': ('wide',),
            'fields': ('organization', 'entry_by', 'updated_by', 'status', )}
        ),
    )

    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter + (
        'account',
    )
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'account__name',
        'reference_name', 'id'
    )
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'account', 'reference_name',
        'condition', 'alias',
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'account',
    )

admin.site.register(AccountCheque, AccountChequeAdmin)


class TransactionPurchaseInline(admin.TabularInline):
    model = Transaction.purchases.through
    raw_id_fields = ('organization', 'entry_by', 'updated_by', 'purchase')


class TransactionAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    inlines = [
        TransactionPurchaseInline,
    ]
    fieldsets = (
        ('Transaction Details', {
            'classes': ('wide',),
            'fields': ('organization', 'accounts', 'department', 'date',
                       'head', 'amount', 'paid_in_note', 'paid_by',
                       'received_by', 'code', 'vouchar_no', 'remarks')}
        ),

        ('Cheque / Bank Draft / Mobile Banking Details', {
            'classes': ('wide',),
            'fields': ('method', 'bank', 'branch', 'account_cheque', 'recipt_no')}
        ),

        ('Transaction For', {
            'classes': ('wide',),
            'fields': (
                'transaction_for', 'admission', 'service_consumed',
                'service_consumed_group', 'sales', 'appointment',
            )}
        ),

        ('Status', {
            'classes': ('wide',),
            'fields': ('entry_by', 'updated_by', 'status', )}
        ),
    )
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter + (
        'accounts',
        'method',
    )
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'accounts__name', 'head__name',
        'paid_by__first_name', 'paid_by__last_name',
        'received_by__first_name', 'received_by__last_name', 'code', 'alias'
    )
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'date', 'head', 'received', 'paid',
        'paid_by', 'accounts', 'code', 'vouchar_no', 'alias'
    )

    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'accounts', 'head', 'paid_by', 'person_organization',
        'admission', 'received_by', 'person_organization_received',
        'service_consumed', 'service_consumed_group', 'sales', 'department',
        'appointment', 'account_cheque',
    )

    def received(self, obj):
        if obj.amount >= 0:
            return obj.amount
        return 0

    def paid(self, obj):
        if obj.amount < 0:
            return -obj.amount
        return 0

admin.site.register(Transaction, TransactionAdmin)


class TransactionHeadAdmin(NameSlugDescriptionBaseOrganizationWiseModelAdmin):

    fieldsets = (
        ('Transaction Details', {
            'classes': ('wide',),
            'fields': ('organization', 'name', 'group', 'department')}
        ),

        ('Status', {
            'classes': ('wide',),
            'fields': ('entry_by', 'updated_by', 'status', 'is_global')}
        ),
    )
    list_filter = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_filter + (
        'group', 'department'
    )
    search_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.search_fields + (
        'department__name',
    )
    list_display = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_display + (
        'group', 'department', 'alias'
    )
    raw_id_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.raw_id_fields + (
        'department',
    )

admin.site.register(TransactionHead, TransactionHeadAdmin)


class PayableToPersonAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    fieldsets = (
        ('Payable To Person Details', {
            'classes': ('wide',),
            'fields': ('organization', 'person', 'person_organization',
                       'transaction_head', 'date', 'amount')}
        ),

        ('Status', {
            'classes': ('wide',),
            'fields': ('entry_by', 'updated_by', 'status', )}
        ),
    )
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'person', 'date', 'transaction_head',
        'group_id', 'amount',
    )
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'group_id', 'person__first_name',
        'person__last_name', 'person__phone', 'person__code'
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'person', 'person_organization',
        'transaction_head',
    )

admin.site.register(PayableToPerson, PayableToPersonAdmin)


class TransactionPurchaseAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    fieldsets = (
        ('Transaction Purchase Details', {
            'classes': ('wide',),
            'fields': ('organization', 'transaction', 'purchase', 'amount')}
        ),

        ('Status', {
            'classes': ('wide',),
            'fields': ('entry_by', 'updated_by', 'status', )}
        ),
    )
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'transaction', 'purchase',
        'amount',
    )
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter + (
        'purchase__purchase_type',
    )
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'transaction__paid_by__first_name', 'transaction__id',
        'transaction__paid_by__last_name', 'transaction__paid_by__phone',
        'transaction__paid_by__code', 'purchase__vouchar_no', 'purchase__id'
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'transaction', 'purchase',
    )

admin.site.register(TransactionPurchase, TransactionPurchaseAdmin)


class PatientBillAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    fieldsets = (
        ('Patient Bill Details', {
            'classes': ('wide',),
            'fields': ('organization', 'person_organization_patient', 'date',
                       'partial_payment_amount', 'total', 'discount', 'remarks')
            }
        ),

        ('Status', {
            'classes': ('wide',),
            'fields': ('entry_by', 'updated_by', 'payment_status', 'status',)}
        ),
    )
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'person_organization_patient',
        'date', 'payment_status',
        'partial_payment_amount', 'total', 'discount',
    )
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter + (
        'payment_status',
    )
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'person_organization_patient__first_name',
        'person_organization_patient__last_name', 'person_organization_patient__phone',
        'person_organization_patient__code', 'id'
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'person_organization_patient',
    )

admin.site.register(PatientBill, PatientBillAdmin)

# to-do : change this class name
class PatientBillTransaction(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'transaction',
        'bill', 'amount',
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'transaction', 'bill',
    )


admin.site.register(BillTransaction, PatientBillTransaction)



class OrganizationWiseOmisServiceAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display


admin.site.register(OrganizationWiseOmisService, OrganizationWiseOmisServiceAdmin)


class OrganizationWiseOmisServiceBillAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display


admin.site.register(OrganizationWiseOmisServiceBill, OrganizationWiseOmisServiceBillAdmin)


class TransactionPayablePersonAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter + (
        'person_payable__type',
    )
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'person_payable__group_id', 'transaction__person_organization__first_name',
        'transaction__person_organization__last_name', 'transaction__person_organization__code',
    )

admin.site.register(TransactionPayablePerson, TransactionPayablePersonAdmin)


class SalesTransactionAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass

admin.site.register(SalesTransaction, SalesTransactionAdmin)
