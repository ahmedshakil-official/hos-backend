import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand
from common.enums import PublishStatus
from core.models import Organization
from ...tests import ProductFactory

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, **options):
        for i in tqdm(range(0, 100000)):
            ProductFactory(
                is_global=PublishStatus.INITIALLY_GLOBAL,
                is_salesable=True,
                organization=Organization.objects.get(pk=2)
            )