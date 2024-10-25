from django.db import models
from django.utils.translation import gettext as _

from enumerify.enum import Enum


class ShortReturnLogType(Enum):
    SHORT = 1
    RETURN = 2

    i18n = (
        _('Short'),
        _('Return'),
    )


class FailedDeliveryReason(Enum):
    UNABLE_TO_REACH = 1
    UNABLE_TO_FIND_ADDRESS = 2
    SHOP_CLOSED = 3
    OTHER = 4
    DEFAULT = 5

    i18n = (
        _('Unable to Reach'),
        _('Unable to Find Address'),
        _('Shop Closed'),
        _('Other'),
        _('Default'),
    )


class TopSheetType(models.TextChoices):
    DEFAULT = "DEFAULT", "Default"
    SUB_TOP_SHEET = "SUB_TOP_SHEET", "Sub Top Sheet"
    DISTRIBUTOR_TOP_SHEET = "DISTRIBUTOR_TOP_SHEET", "Distributor Top Sheet"


class AssignedUnassignedState(Enum):
    Assigned = "assigned"
    Unassigned = "unassigned"