from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from account.tests import TransactionFactory, AccountFactory
from clinic.tests import AppointmentTreatmentSessionFactory

from . import PatientFactory
