import json
from faker import Faker

from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status

from core.tests import ReferrerFactory
from core.enums import PersonGroupType
from core.models import PersonOrganization

