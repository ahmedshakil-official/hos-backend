import random

from faker import Faker
from django.urls import reverse

from common.test_case import OmisTestCase


from ..enums import (
    SalaryHeadType,
    SalaryHeadDisburseType,
)
from ..tests import SalaryHeadFactory

