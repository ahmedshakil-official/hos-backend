from faker import Faker
import uuid
from django.urls import reverse
from common.utils import inactive_instance
from common.test_case import OmisTestCase
from core.tests import OrganizationFactory
from core.enums import OrganizationType