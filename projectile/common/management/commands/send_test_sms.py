import logging

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from ...tasks import send_sms

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sends test SMS using celery worker"

    def handle(self, **options):
        logger.info("Sending Test SMS...")

        for phone_number in settings.TEST_PHONE_NUMBERS:
            send_sms.delay(phone_number, 'HealthOS Test SMS on {}'.format(
                timezone.now().strftime("%A  %H:%M:%S %d-%B-%Y"),
            ), settings.TEST_SMS_ORGANIZATION_ID)

        logger.info("Test SMS Sent.")
