from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status

from account.tests import TransactionFactory
from clinic.tests import (
    AppointmentTreatmentSessionFactory,
    AppointmentScheduleFactory,
    PatientAdmissionFactory,
    ServiceConsumedFactory,
)
from pharmacy.tests import SalesFactory
from prescription.tests import PrescriptionFactory

from core.models import Person
from . import PatientFactory, PersonFactory

