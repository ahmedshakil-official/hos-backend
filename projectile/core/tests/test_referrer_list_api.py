import random
from faker import Faker
from django.urls import reverse

from common.utils import inactive_instance
from common.test_case import OmisTestCase
from core.tests import PersonFactory
from core.enums import PersonGroupType
