import json
import random
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from core.tests import ServiceProviderFactory

from ..models import Person
from ..enums import PersonGroupType


