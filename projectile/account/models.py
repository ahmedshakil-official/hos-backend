from __future__ import unicode_literals

from enumerify import fields
from django.db import models
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save, pre_save
from common.validators import validate_non_zero_amount
from common.enums import DiscardType, Status
from common.models import (
    NameSlugDescriptionBaseOrganizationWiseModel,
    CreatedAtUpdatedAtBaseModelWithOrganization
)
from core.models import Person, PersonOrganization
from pharmacy.models import Sales
from clinic.models import (
    ServiceConsumed,
    PatientAdmission,
    AppointmentTreatmentSession,
    ServiceConsumedGroup
)

from .enums import (
    TransactionMethod,
    TransactionHeadGroup,
    AccountType,
    TransactionHeadType,
    TransactionFor,
    AccountChequeType,
    PayablePersonType,
    BillPaymentStatus,
    OmisServices,
    NatureOfService,
)

class Accounts(NameSlugDescriptionBaseOrganizationWiseModel):
    type = fields.SelectIntegerField(blueprint=AccountType)
    opening_balance = models.FloatField(default=0)
    balance = models.FloatField(default=0)
    bank = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name=('bank name')
    )
    branch = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name=('branch of bank')
    )
    ac_no = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name=('a/c number')
    )

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name_plural = "accounts"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.name)

    @property
    def current_balance(self):
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        transactions = self.transaction_set.filter(
            organization_id=self.organization_id,
            status=Status.ACTIVE,
        ).aggregate(
            total_balance=Coalesce(Sum('amount'), 0.0)
        )
        return transactions.get('total_balance', 0) + self.opening_balance
        # query = '''
        #     SELECT accounts_id as id,
        #         Sum(amount) AS total_balance
        #     FROM   account_transaction
        #     WHERE  organization_id = {}
        #         AND accounts_id = {}
        #         AND status = {}
        #     GROUP  BY ( accounts_id )
        #     LIMIT  1
        # '''
        # query = query.format(
        #     self.organization.id,
        #     self.id,
        #     Status.ACTIVE
        # )
        # account = Accounts.objects.raw(query)
        # if account:
        #     return account[0].total_balance + self.opening_balance
        # return self.opening_balance


class AccountCheque(CreatedAtUpdatedAtBaseModelWithOrganization):
    account = models.ForeignKey(
        'Accounts', models.DO_NOTHING, related_name='account_cheque')
    reference_name = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name=('reference name'),
        db_index=True,
        default=None
    )
    condition = fields.SelectIntegerField(
        blueprint=AccountChequeType,
        verbose_name=('group of conditions')
    )

    class Meta:
        verbose_name_plural = "account cheques"
        index_together = (
            'organization',
            'status',
            'account'
        )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.account_id)


class TransactionGroup(CreatedAtUpdatedAtBaseModelWithOrganization):
    code = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=('unique code for group transaction')
    )
    amount = models.FloatField(default=0.0)
    serial_no = models.PositiveIntegerField(
        default=None, blank=True, null=True, help_text='Serial Number')

    class Meta:
        verbose_name_plural = "transaction group"

    def get_name(self):
        return u"#{}: {}".format(self.id, self.code)


class Transaction(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateTimeField()
    head = models.ForeignKey('TransactionHead', models.DO_NOTHING)
    amount = models.FloatField(validators=[validate_non_zero_amount])
    paid_in_note = models.FloatField(default=0.0)

    transaction_for = fields.SelectIntegerField(
        blueprint=TransactionFor,
        default=TransactionFor.OTHER
    )
    transaction_group = models.ForeignKey(
        TransactionGroup, models.DO_NOTHING,
        related_name='transaction_group',
        blank=True,
        null=True,
        verbose_name=('transaction group'),
        db_index=True
    )
    # this is the person who is organization dealing with
    paid_by = models.ForeignKey(
        Person, models.DO_NOTHING,
        related_name='paying_by',
        blank=True,
        null=True,
        verbose_name=('transaction by'),
        db_index=True
    )
    person_organization = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='paid_by_person_organization',
        blank=True,
        null=True,
        verbose_name=('transaction by person of organization'),
        db_index=True
    )
    # representetive of organization
    received_by = models.ForeignKey(
        Person,
        models.DO_NOTHING,
        related_name='receive_by',
        blank=True,
        null=True,
        verbose_name=('employee'),
        db_index=True
    )

    person_organization_received = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='received_by_person_organization',
        blank=True,
        null=True,
        verbose_name=('employee person organization'),
        db_index=True
    )

    service_consumed = models.ForeignKey(
        ServiceConsumed,
        models.DO_NOTHING,
        related_name='service_consumed_transaction',
        blank=True,
        null=True,
        default=None,
        verbose_name=('for service consumption of'),
        db_index=True
    )
    service_consumed_group = models.ForeignKey(
        ServiceConsumedGroup,
        models.DO_NOTHING,
        related_name='service_consumed_group_transaction',
        blank=True,
        null=True,
        default=None,
        verbose_name=('for group service consumption of'),
        db_index=True
    )
    admission = models.ForeignKey(
        PatientAdmission,
        models.DO_NOTHING,
        related_name='admission_transaction',
        blank=True,
        null=True,
        default=None,
        verbose_name=('for admission of'),
        db_index=True
    )
    appointment = models.ForeignKey(
        AppointmentTreatmentSession,
        models.DO_NOTHING,
        related_name='appointment_transaction',
        blank=True,
        null=True,
        default=None,
        verbose_name=('for appointment of'),
        db_index=True
    )

    method = fields.SelectIntegerField(
        blueprint=TransactionMethod,
        verbose_name=('method of transaction'),
        db_index=True
    )
    remarks = models.CharField(max_length=255, blank=True, null=True)
    accounts = models.ForeignKey(
        Accounts,
        models.DO_NOTHING,
        verbose_name=('a/c'),
        db_index=True
    )
    sales = models.ForeignKey(
        Sales,
        models.DO_NOTHING,
        related_name='transaction_of',
        blank=True,
        null=True,
        verbose_name=('for sales of'),
        db_index=True
    )
    tagged_sales = models.ManyToManyField(
        Sales, through='account.SalesTransaction',
        related_name='transactions_tagged_sales'
    )
    code = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=('unique code for group transaction')
    )

    bank = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name=('bank or mobile banking provider')
    )

    branch = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name=('branch if any')
    )

    account_cheque = models.ForeignKey(
        AccountCheque,
        models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name=('account cheque'),
        related_name='accoun_cheque_of',
        db_index=True
    )

    recipt_no = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name=('cheque, bank draft or reference no')
    )

    vouchar_no = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        default=None
    )

    purchases = models.ManyToManyField(
        'pharmacy.Purchase', through='account.TransactionPurchase',
        related_name='purchases_transaction'
    )

    person_payables = models.ManyToManyField(
        'account.PayableToPerson', through='account.TransactionPayablePerson',
        related_name='person_payable_transaction'
    )

    department = models.ForeignKey(
        'clinic.OrganizationDepartment', models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        db_index=True,
        related_name='transaction',
        verbose_name=('department of transaction')
    )
    bills = models.ManyToManyField(
        'account.PatientBill', through='account.BillTransaction',
        related_name='bills_transaction'
    )
    amount_payable = models.FloatField(default=0.0)
    discount = models.FloatField(default=0.0)
    previous_paid = models.FloatField(default=0.0)
    previous_due = models.FloatField(default=0.0)
    current_due = models.FloatField(default=0.0)

    # pylint: disable=old-style-class, no-init

    class Meta:
        verbose_name_plural = "Transactions"
        index_together = [
            ["date"],
            ["date", "accounts", "head", "method"],
            ["date", "received_by"],
            ["date", "paid_by"],
        ]

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.date, self.paid_by_id)


class TransactionHead(NameSlugDescriptionBaseOrganizationWiseModel):
    type = fields.SelectIntegerField(
        blueprint=TransactionHeadType,
        default=TransactionHeadType.CAPITAL,
        verbose_name=('type of head')
    )
    group = fields.SelectIntegerField(
        blueprint=TransactionHeadGroup,
        verbose_name=('group of transaction head')
    )

    department = models.ForeignKey(
        'clinic.OrganizationDepartment', models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        db_index=True,
        related_name='transaction_head',
        verbose_name=('department of transaction head')
    )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.name)


class OrganizationWiseDiscardedTransactionHead(CreatedAtUpdatedAtBaseModelWithOrganization):
    # current usage item
    head = models.ForeignKey(
        TransactionHead, models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='organization_wise_discarded_head'
    )
    # edited, merged or deleted item
    parent = models.ForeignKey(
        TransactionHead,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='organization_wise_discarded_parent_head'
    )
    entry_type = fields.SelectIntegerField(
        blueprint=DiscardType, default=DiscardType.EDIT)
    # pylint: disable=old-style-class, no-init
    class Meta:
        index_together = (
            'organization',
            'head',
        )
        verbose_name_plural = "Organization's Discarded Head"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"Organization: {}, Base: {}, Product: {}".format(
            self.organization_id,
            self.head_id,
            self.parent_id
        )


class PayableToPerson(CreatedAtUpdatedAtBaseModelWithOrganization):
    person = models.ForeignKey(
        Person, models.DO_NOTHING,
        related_name='payable_person',
        blank=False,
        null=False,
        db_index=True
    )
    date = models.DateField(blank=False, null=False)
    person_organization = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='payable_person_organization',
        blank=False,
        null=False,
        verbose_name=('person organization'),
        db_index=True
    )
    transaction_head = models.ForeignKey(
        TransactionHead, models.DO_NOTHING,
        related_name='payable_transaction_head',
        blank=False,
        null=False,
        verbose_name=('transaction head'),
        db_index=True
    )
    amount = models.FloatField(validators=[validate_non_zero_amount])
    group_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        editable=False,
        verbose_name=('unique code for group payable')
    )
    type = fields.SelectIntegerField(
        blueprint=PayablePersonType,
        default=PayablePersonType.ADDITION,
        verbose_name=('payable type')
    )
    paid = models.FloatField(default=0.00, validators=[MinValueValidator(0.00)])
    paid_status = fields.SelectIntegerField(
        blueprint=BillPaymentStatus,
        default=BillPaymentStatus.DUE,
        verbose_name=('paid status')
    )

    # pylint: disable=old-style-class, no-init

    class Meta:
        verbose_name = "Payable To Person"
        verbose_name_plural = "Payable To Persons"
        index_together = ["organization", "status"],

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {} / {}".format(self.id, self.person_id,
                                           self.transaction_head_id,
                                           self.amount)


class TransactionPurchase(CreatedAtUpdatedAtBaseModelWithOrganization):
    transaction = models.ForeignKey(
        Transaction, models.DO_NOTHING,
        blank=False, null=False, db_index=True,
        related_name='purchase_transaction'
    )
    purchase = models.ForeignKey(
        'pharmacy.Purchase', models.DO_NOTHING,
        blank=True, null=True, db_index=True,
        related_name='transaction_purchase'
    )
    amount = models.FloatField(default=0)

    # pylint: disable=old-style-class, no-init

    class Meta:
        verbose_name = "Purchase To Transaction"
        verbose_name_plural = "Purchase To Transactions"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.transaction_id, self.purchase_id)


class TransactionPayablePerson(CreatedAtUpdatedAtBaseModelWithOrganization):
    transaction = models.ForeignKey(
        Transaction, models.DO_NOTHING,
        blank=False, null=False, db_index=True,
        related_name='payable_transaction'
    )
    person_payable = models.ForeignKey(
        'account.PayableToPerson', models.DO_NOTHING,
        blank=True, null=True, db_index=True,
        related_name='transaction_payable'
    )
    amount = models.FloatField(default=0)

    # pylint: disable=old-style-class, no-init

    class Meta:
        verbose_name = "Payable Person To Transaction"
        verbose_name_plural = "Payables Person To Transactions"

    def __unicode__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.transaction, self.person_payable)


class PatientBill(CreatedAtUpdatedAtBaseModelWithOrganization):
    person_organization_patient = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='patient_bill_person_organization',
        blank=True,
        null=True,
        verbose_name=('patient in person organization'),
        db_index=True
    )
    date = models.DateTimeField(blank=True, null=True)
    payment_status = fields.SelectIntegerField(
        blueprint=BillPaymentStatus,
        default=BillPaymentStatus.DUE,
        verbose_name=('payment status')
    )
    partial_payment_amount = models.FloatField(default=0.0)
    total = models.FloatField(default=0.0)
    discount = models.FloatField(default=0.0)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Patient Bill"
        verbose_name_plural = "Patient Bills"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.person_organization_patient_id, self.date)


class BillTransaction(CreatedAtUpdatedAtBaseModelWithOrganization):
    transaction = models.ForeignKey(
        Transaction, models.DO_NOTHING,
        blank=False, null=False, db_index=True,
        related_name='bill_transaction'
    )
    bill = models.ForeignKey(
        'account.PatientBill', models.DO_NOTHING,
        blank=True, null=True, db_index=True,
        related_name='transaction_bill'
    )
    amount = models.FloatField(default=0)

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Bill To Transaction"
        verbose_name_plural = "Bill To Transactions"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.transaction_id, self.bill_id)


class SalesTransaction(CreatedAtUpdatedAtBaseModelWithOrganization):
    transaction = models.ForeignKey(
        Transaction, models.DO_NOTHING,
        blank=False, null=False, db_index=True,
        related_name='sales_transactions_transactions'
    )
    sales = models.ForeignKey(
        Sales, models.DO_NOTHING,
        blank=True, null=True, db_index=True,
        related_name='sales_transactions_sales'
    )
    amount = models.FloatField(default=0)

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Sales To Transaction"
        verbose_name_plural = "Sales To Transactions"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.transaction_id, self.sales_id)


class OrganizationWiseOmisService(CreatedAtUpdatedAtBaseModelWithOrganization):

    service = fields.SelectIntegerField(
        blueprint=OmisServices,
        default=OmisServices.INSTALLATION,
        verbose_name=('type of service')
    )
    kind = fields.SelectIntegerField(
        blueprint=NatureOfService,
        default=NatureOfService.ONE_TIME,
        verbose_name=('nature of service'),
    )
    amount = models.FloatField(default=0)
    billing_frequency = models.SmallIntegerField(
        default=0, blank=False, null=False,
    )
    start_date = models.DateTimeField()
    description = models.TextField(blank=True)

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Organization-wise Service"
        verbose_name_plural = "Organization-wise Service"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.organization_id, self.kind)


class OrganizationWiseOmisServiceBill(CreatedAtUpdatedAtBaseModelWithOrganization):
    billing_date = models.DateTimeField()
    bill_for_service = models.ForeignKey(
        OrganizationWiseOmisService, models.DO_NOTHING,
        blank=False, null=False, db_index=True,
        related_name='omis_bill_for_services'
    )
    amount = models.FloatField(default=0)
    paid_amount = models.FloatField(default=0)
    discount_amount = models.FloatField(default=0)
    is_published = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    due_date = models.DateTimeField()
    billing_cycle_on = models.BooleanField(default=False)
    next_date = models.DateTimeField(blank=True, null=True,)
    previous_bill = models.ForeignKey(
        'self', models.DO_NOTHING,
        blank=True, null=True, db_index=True,
        related_name='previous_omis_bill'
    )
    next_bill = models.ForeignKey(
        'self', models.DO_NOTHING,
        blank=True, null=True, db_index=True,
        related_name='next_omis_bill'
    )
    description = models.TextField(blank=True)

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Organizationwise Bill"
        verbose_name_plural = "Organizationwise Bills"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.organization_id, self.bill_for_service_id)

