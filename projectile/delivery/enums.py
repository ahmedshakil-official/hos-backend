from django.utils.translation import gettext as _

from enumerify.enum import Enum


class DeliveryTrackingStatus(Enum):
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
        _('Full Returned')
    )
