from django.utils.translation import gettext as _
from django.db import models

from enumerify.enum import Enum

class StorePointType(Enum):
    GODOWN = 0
    PHARMACY = 1
    VENDOR = 2
    VENDOR_DEFAULT = 3

    i18n = (
        _('Godown'),
        _('Pharmacy'),
        _('Vendor'),
        _('Vendor Default'),
    )


class StockIOType(Enum):
    INPUT = 0
    OUT = 1  # please don't change it to -1, it's acting strange that way

    i18n = (
        _('IN'),
        _('OUT'),
    )


class ProductGroupType(Enum):
    MEDICINE = 0
    OTHER = 1

    i18n = (
        _('Medicine'),
        _('Other'),
    )


class SalesType(Enum):
    RETAIL_CASH = 1
    RETAIL_CREDIT = 2
    WHOLE_SALE_CASH = 3
    WHOLE_SALE_CREDIT = 4

    i18n = (
        _('Retail Cash'),
        _('Retail Credit'),
        _('Whole Sale Cash'),
        _('Whole Sale Credit'),
    )


class SalesInactiveType(Enum):
    FROM_ACTIVE = 1
    FROM_ON_HOLD = 2
    FROM_EDIT = 3

    i18n = (
        _('From Active'),
        _('From On Hold'),
        _('From Edit'),
    )


class TransferStatusType(Enum):
    PROPOSED_TRANSFER = 0
    APPROVED = 1

    i18n = (
        _('Proposed Transfer'),
        _('Approved'),
    )


class PurchaseType(Enum):
    REQUISITION = 1
    ORDER = 2
    PURCHASE = 3
    VENDOR_ORDER = 4

    i18n = (
        _('Requisition'),
        _('Order'),
        _('Purchase'),
        _('Vendor Order'),
    )


class PurchaseOrderStatus(Enum):
    DEFAULT = 1
    PENDING = 2
    COMPLETED = 3
    DISCARDED = 4

    i18n = (
        _('Default'),
        _('Pending'),
        _('Completed'),
        _('Discarded'),
    )

class DisbursementFor(Enum):
    DEFAULT = 1
    PATIENT = 2
    SERVICE_CONSUMED = 3

    i18n = (
        _('Default'),
        _('Patient'),
        _('Service Consumed'),
    )


class AdjustmentType(Enum):
    MANUAL = 1
    AUTO = 2
    OTHER = 3

    i18n = (
        _('Manual'),
        _('Auto'),
        _('Other'),
    )


class SalesModeType(Enum):
    ONLINE = 1
    OFFLINE = 2
    OTHER = 3

    i18n = (
        _('Online'),
        _('Offline'),
        _('Other'),
    )

class InventoryType(Enum):
    SALES = 1
    PURCHASE = 2
    ADJUSTMENT_IN = 3
    ADJUSTMENT_OUT = 4
    TRANSFER_IN = 5
    TRANSFER_OUT = 6
    DISBURSEMENT = 7

    i18n = (
        _('Sales'),
        _('Purchase'),
        _('Adjustment In'),
        _('Adjustment Out'),
        _('Transfer In'),
        _('Transfer Out'),
    )

class GlobalProductCategory(Enum):
    DEFAULT = 1
    GPA = 2
    GPB = 3

    i18n = (
        _('Default'),
        _('GPA'),
        _('GPB'),
    )


class DataEntryStatus(Enum):
    NOT_COUNTED = 1
    COUNTED = 2
    DONE = 3

    i18n = (
        _('Not Counted'),
        _('Counted'),
        _('Done'),
    )


class DistributorOrderType(Enum):
    CART = 1
    ORDER = 2

    i18n = (
        _('Cart'),
        _('Order'),
    )


class OrderTrackingStatus(Enum):
    PENDING = 1
    ACCEPTED = 2
    READY_TO_DELIVER = 3
    ON_THE_WAY = 4
    DELIVERED = 5
    COMPLETED = 6
    REJECTED = 7
    CANCELLED = 8
    PARITAL_DELIVERED = 9
    FULL_RETURNED = 10
    IN_QUEUE = 11
    PORTER_DELIVERED = 12
    PORTER_FULL_RETURN = 13
    PORTER_PARTIAL_DELIVERED = 14
    PORTER_FAILED_DELIVERED = 15

    i18n = (
        _('Pending'),
        _('Accepted'),
        _('Ready to Deliver'),
        _('On the Way'),
        _('Delivered'),
        _('Completed'),
        _('Rejected'),
        _('Cancelled'),
        _('Partial Delivered'),
        _('Full Returned'),
        _('In Queue'),
        _('Porter Delivered'),
        _('Porter Full Return'),
        _('Porter Partial Delivered'),
        _('Porter Failed Delivered')
    )


class SystemPlatforms(Enum):
    UN_IDENTIFIED = 1
    WEB_APP = 2
    ANDROID_APP = 3
    IOS_APP = 4
    ECOM_WEB = 5
    PROCUREMENT_WEB = 6

    i18n = (
        _('Un Identified'),
        _('Web App'),
        _('Android App'),
        _('IOS App'),
        _('E-commerce Web'),
        _('Procurement Web'),
    )


class UnitType(Enum):
    BOX = 1
    STRIP = 2
    BOX_AND_STRIP = 3

    i18n = (
        _('Box'),
        _('Strip'),
        _('Box and Strip'),
    )


class DamageProductType(models.TextChoices):
    RETURN_DAMAGE = "RETURN_DAMAGE", "Return Damage"
    DISTRIBUTION_DAMAGE = "DISTRIBUTION_DAMAGE", "Distribution Damage"


class RecheckProductType(models.TextChoices):
    EXTRA = "EXTRA", "Extra"
    MISSING = "MISSING", "Missing"
