from django.utils.translation import gettext as _

from enumerify.enum import Enum


class TransactionMethod(Enum):
    CASH = 1
    CHEQUE = 2
    MOBILE_BANKING = 3
    BANK_DRAFT = 4
    CARD = 5

    i18n = (
        _('Cash'),
        _('Cheque'),
        _('Mobile Banking'),
        _('Bank Draft'),
        _('Card'),
    )


class TransactionHeadGroup(Enum):
    PATIENT = 1
    EMPLOYEE = 2
    SUPPLIER = 3
    STACK_HOLDER = 4
    REFERRER = 5
    OTHER = 6
    SERVICE_PROVIDER = 7

    i18n = (
        _('Patient'),
        _('Employee'),
        _('Supplier'),
        _('Stack Holder'),
        _('Referrer'),
        _('Other'),
        _('Service Provider'),
    )


class AccountType(Enum):
    CASH = 1
    BANK = 2

    i18n = (
        _('Cash'),
        _('Bank'),
    )


class TransactionHeadType(Enum):
    CAPITAL = 1
    RECURRING = 2

    i18n = (
        _('Capital'),
        _('Recurring'),
    )


class TransactionFor(Enum):
    SALE = 1
    ADMISSION = 2
    APPOINTMENT = 3
    SERVICE_CONSUMED = 4
    OTHER = 5
    PURCHASE = 6
    PERSON_PAYABLE = 7

    i18n = (
        _('Sale'),
        _('Admission'),
        _('Appointment'),
        _('Service Consumed'),
        _('Others'),
        _('Purchase'),
        _('Person Payable'),
    )


class AccountChequeType(Enum):
    USED = 1
    UNUSED = 2
    RETURNED = 3

    i18n = (
        _('Used'),
        _('Unused'),
        _('Returned'),
    )


class PayablePersonType(Enum):
    ADDITION = 1
    DEDUCTION = 2
    OTHER = 3

    i18n = (
        _('Addition'),
        _('Deduction'),
        _('Other'),
    )


class TransactionType(Enum):
    PAYING = -1
    RECEIVING = 1

    i18n = (
        _('Paying'),
        _('Receiving')
    )


class BillPaymentStatus(Enum):
    DUE = 1
    PAID = 2
    PARTIAL = 3

    i18n = (
        _('Due'),
        _('Paid'),
        _('Partial'),
    )


class OmisServices(Enum):
    INSTALLATION = 1
    DATA_ENTRY = 2
    TRAINING = 3
    MONTHLY_SERVICE_CHARGE = 4
    CUSTOM_SERVICE = 5

    i18n = (
        _('Installation'),
        _('Data Entry'),
        _('Training'),
        _('Monthly Service Charge'),
        _('Custom Services'),
    )

class NatureOfService(Enum):
    ONE_TIME = 1
    LIMITED_FREQUENT_TIME = 2
    PREODIC = 3

    i18n = (
        _('One Time'),
        _('Limited Time'),
        _('Periodic'),
    )
