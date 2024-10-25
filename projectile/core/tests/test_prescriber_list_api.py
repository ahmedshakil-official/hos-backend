import json
import random

from django.urls import reverse
from faker import Faker

from common.utils import inactive_instance
from common.test_case import OmisTestCase
from core.enums import PersonGroupType, PersonType
from core.models import PersonOrganization, PersonOrganizationGroupPermission
from . import (
    EmployeeFactory,
    GroupPermissionFactory,
    PersonOrganizationGroupPermissionFactory,
)
