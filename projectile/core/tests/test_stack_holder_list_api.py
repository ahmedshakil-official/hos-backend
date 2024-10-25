import random
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status

from common.utils import inactive_instance
from core.models  import PersonOrganization
from core.tests import PersonFactory
from core.enums import PersonGroupType
