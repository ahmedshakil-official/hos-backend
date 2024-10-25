from django.utils.translation import gettext as _
from enumerify.enum import Enum


class PublishStatus(Enum):
    PRIVATE = 0
    INITIALLY_GLOBAL = 1
    WAS_PRIVATE_NOW_GLOBAL = 2

    i18n = (
        _('Private'),
        _('Global'),
        _('Changed into Global'),
    )


class Status(Enum):
    ACTIVE = 0
    INACTIVE = 1
    DRAFT = 2
    RELEASED = 3
    APPROVED_DRAFT = 4
    ABSENT = 5
    PURCHASE_ORDER = 6
    SUSPEND = 7
    ON_HOLD = 8
    HARDWIRED = 9
    LOSS = 10
    FREEZE = 11
    FOR_ADJUSTMENT = 12
    DISTRIBUTOR_ORDER = 13

    i18n = (
        _('Active'),
        _('Inactive'),
        _('Draft'),
        _('Released'),
        _('Approved Draft'),
        _('Absent'),
        _('Purchase Order'),
        _('Suspend'),
        _('On Hold'),
        _('Hardwired'),
        _('Loss'),
        _('Freeze'),
        _('For Adjustment'),
        _('Distributor Order'),
    )


class SmsLogType(Enum):
    DATABASE = 1
    CSV_FILE = 2

    i18n = (
        _('Database'),
        _('CSV file'),
    )


class DiscardType(Enum):
    EDIT = 1
    MERGE = 2
    OTHER = 3

    i18n = (
        _('Edit'),
        _('Merge'),
        _('Other'),
    )


class GlobalCategory(Enum):
    DEFAULT = 1
    CATEGORY_A = 2
    CATEGORY_B = 3

    i18n = (
        _('Default'),
        _('Category A'),
        _('Category B'),
    )


class ReportType(Enum):
    GROUP_WISE_SALE_SUMMARY = 1
    GROUP_WISE_PURCHASE_SUMMARY = 2
    GROUP_WISE_STOCK_VALUE_SUMMARY = 3

    i18n = (
        _('Group Wise Sale Summary'),
        _('Group Wise Purchase Summary'),
        _('Group Wise Stock Value Summary'),
    )


class ActionType(Enum):
    CREATE = 1
    UPDATE = 2
    DELETE = 3

    i18n = (
        _('Create'),
        _('Update'),
        _('Delete'),
    )
