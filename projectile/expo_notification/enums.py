from django.utils.translation import gettext as _

from enumerify.enum import Enum


class DeviceType(Enum):
    ANDROID = 1
    IOS = 2
    OTHERS = 3

    i18n = (
        _('Android'),
        _('Ios'),
        _('Others'),
    )
