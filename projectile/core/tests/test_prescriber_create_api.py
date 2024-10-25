import random
from faker import Faker
from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status

from . import PersonFactory, DesignationFactory
from ..enums import PersonGroupType, PersonGender, PersonType
from ..models import Person, PersonOrganization

