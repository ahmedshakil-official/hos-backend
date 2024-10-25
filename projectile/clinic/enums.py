from django.utils.translation import gettext as _
from enumerify.enum import Enum


class ServiceType(Enum):
    DIAGNOSTIC = 1
    OTHERS = 2

    i18n = (
        _('Diagnostic'),
        _('Others'),
    )


class DaysChoice(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    i18n = (
        _('Monday'),
        _('Tuesday'),
        _('Wednesday'),
        _('Thursday'),
        _('Friday'),
        _('Saturday'),
        _('Sunday'),
    )


class BedStatus(Enum):
    FREE = 0
    ENGAGED = 1

    i18n = (
        _('Free'),
        _('Engaged'),
    )


class ConfirmedType(Enum):
    PATIENT_CREATED_BUT_YET_UNAPPROVED = 1
    DR_CREATED_BUT_YET_UNAPPROVED = 2
    APPROVED_BY_BOTH = 3

    i18n = (
        _('Patient Created But Yet Unapproved'),
        _('Dr. Created But Yet Unapproved'),
        _('Approved By Both'),
    )


class PatientAdmissionBedStatus(Enum):
    INITIALLY_MOVED = 1
    TRANSFERED_FROM_OTHER_BED = 2
    CHECKED_OUT = 3

    i18n = (
        _('Admitted'),
        _('Transfered'),
        _('Checkedout'),
    )


class EmployeeAttendanceType(Enum):
    DEFAULT = 0
    ENTRY = 1
    EXIT = 2

    i18n = (
        _('Default'),
        _('Entry'),
        _('Exit'),
    )


class ServiceConsumedPriority(Enum):
    NORMAL = 0
    LOW = 1
    HIGH = 2

    i18n = (
        _('Normal'),
        _('Low'),
        _('High'),
    )


class BedType(Enum):
    ADMISSION_BED = 1
    OPERATION_BED = 2
    CONSULTANT_ROOM = 3

    i18n = (
        _('Admission Bed'),
        _('Operation Bed'),
        _('Consultant Room'),
    )


class ServiceConsumedType(Enum):
    DEFAULT = 1
    PATHOLOGY = 2

    i18n = (
        _('Default'),
        _('Pathology'),
    )


class ServiceConsumedSubType(Enum):
    OTHERS = 1

    i18n = (
        _('Others'),
    )


class PaymentType(Enum):
    CASH = 1
    ADVANCED = 2
    DUE = 3
    PARTIAL = 4
    FREE = 5

    i18n = (
        _('Cash'), # when there is transaction and amount >= service amount
        _('Advanced'), # no transaction and service amount is <= patient balance
        _('Due'), # no transaction and patient balance >= 0
        _('Partial'), # otherwise
        _('Free'), # when service amount is 0
    )


class AppointmentType(Enum):
    CONFIRMED = 1
    REQUEST = 2
    URGENT = 3
    REJECTED = 4

    i18n = (
        _('Confirmed'),
        _('Request'),
        _('Urgent'),
        _('Rejected'),
    )

class PathologyStatus(Enum):
    COMPLETED = 1
    REQUESTED = 2
    SAMPLE_COLLECTED = 3
    SAMPLE_TESTED = 4

    i18n = (
        _('Completed'),
        _('Requested'),
        _('Sample Collected'),
        _('Sample Tested'),
    )


class AppointmentKind(Enum):
    CONSULTATION = 1
    OPERATION = 2

    i18n = (
        _('Consultation'),
        _('Operation'),
    )
