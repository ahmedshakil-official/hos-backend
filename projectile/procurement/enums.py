from django.db.models import TextChoices
from django.utils.translation import gettext as _

from enumerify.enum import Enum


class ProcureType(Enum):
    DEFAULT = 1
    PURCHASE = 2
    ORDER = 3

    i18n = (
        _('Default'),
        _('Purchase'),
        _('Order'),
    )


class ProcureItemType(Enum):
    IN = 1
    OUT = 2

    i18n = (
        _('IN'),
        _('OUT'),
    )


class RateStatus(Enum):
    OK = 1
    LOWER_THAN_RANGE = 2
    HIGHER_THAN_RANGE = 3

    i18n = (
        _('Ok'),
        _('Higher Than Range'),
        _('Lower Than Range'),
    )

class RecommendationPriority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    OTHER = 4

    i18n = (
        _('High'),
        _('Medium'),
        _('Low'),
        _('Other'),
    )


class ProcureIssueType(Enum):
    UN_AVAILABILITY = 1
    RATE_DISCREPANCY = 2
    OTHER = 3

    i18n = (
        _('Unavailability'),
        _('Rate Discrepancy'),
        _('Other'),
    )


class PredictionItemMarkType(Enum):
    MARK = 1
    UN_MARK = 2

    i18n = (
        _('Mark'),
        _('Un Mark'),
    )


class ProcureStatus(Enum):
    DRAFT = 1
    ORDER_PLACED = 2
    PICKED = 3
    DELIVERED = 4
    PAID = 5
    COMPLETED = 6

    i18n = (
        _('Draft'),
        _('Order Placed'),
        _('Picked'),
        _('Delivered'),
        _('Paid'),
        _('Completed'),
    )

class ProcurePlatform(Enum):
    PHYSICAL = 1
    DIGITAL_DEVICE = 2
    OTHER = 3

    i18n = (
        _('Physical'),
        _('Digital Device'),
        _('Other'),
    )


class ReturnReason(TextChoices):
    BROKEN_PRODUCT = "BROKEN_PRODUCT", "Broken Product"
    EXPIRED_PRODUCT = "EXPIRED_PRODUCT", "Expired Product"
    WRONG_PRODUCT = "WRONG_PRODUCT", "Wrong Product"
    OTHER = "OTHER", "Other"


class ReturnCurrentStatus(TextChoices):
    PENDING = "PENDING", "Pending"
    PARTIALLY_SETTLED = "PARTIALLY_SETTLED", "Partially Settled"
    SETTLED = "SETTLED", "Settled"


class ReturnSettlementMethod(TextChoices):
    CASH = "CASH", "Cash"
    CHEQUE = "CHEQUE", "Cheque"
    NET_AGAINST_COMMISSION = "NET_AGAINST_COMMISSION", "Net Against Commission"
    PRODUCT_REPLACEMENT = "PRODUCT_REPLACEMENT", "Product Replacement"


class ProcurePaymentMethod(TextChoices):
    CASH = "CASH", "Cash"
    CHEQUE = "CHEQUE", "Cheque"
    BKASH = "BKASH", "Bkash"
    NAGAD = "NAGAD", "Nagad"


class ProcureDateUpdateType(TextChoices):
    ADVANCE = "ADVANCE", "Advance"
    REVERSE_ADVANCE = "REVERSE_ADVANCE", "Reverse Advance"


class CreditStatusChoices(TextChoices):
    HOLD = "HOLD", "Hold"
    PAID = "PAID", "Paid"
    UNPAID = "UNPAID", "Unpaid"
    PENDING = "PENDING", "Pending"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
