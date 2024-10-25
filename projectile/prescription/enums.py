from django.utils.translation import gettext as _
from enumerify.enum import Enum


class PrescriptionType(Enum):
    NORMAL = 0
    MEDICAL_RECORD = 1

    i18n = (
        _('Normal'),
        _('Medical Record'),
    )


class TestState(Enum):
    PRE = 0
    POST = 1
    DURING = 2

    i18n = (
        _('Pre Operation'),
        _('Post Operation'),
        _('During Operation'),
    )


class PrescriptionPosition(Enum):
    LATEST = 1
    CROSSED_AWAY = 2
    OTHER = 3

    i18n = (
        _('Latest'),
        _('Crossed Away'),
        _('Other'),
    )


class DiagnosisType(Enum):
    CURRENT = 1
    PREVIOUS = 2

    i18n = (
        _('Previous'),
        _('Current'),
    )


class UsageType(Enum):
    ONE_TIME = 1
    TWO_TIME = 2
    ANY = 3

    i18n = (
        _('One Time'),
        _('Two Times'),
        _('Any'),
    )
