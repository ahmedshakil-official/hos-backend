import random

from faker import Faker
from django.urls import reverse

from common.test_case import OmisTestCase
from common.enums import Status, PublishStatus
from ..enums import SalaryDisburseTypes
from ..tests import SalaryGradeFactory, SalaryHeadFactory
