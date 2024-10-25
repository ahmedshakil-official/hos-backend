import json
import random
from django.urls import reverse
from faker import Faker
from common.test_case import OmisTestCase
from core.tests import PersonGroupFactory
from ..enums import PersonGroupType

from ..models import PersonGroup
