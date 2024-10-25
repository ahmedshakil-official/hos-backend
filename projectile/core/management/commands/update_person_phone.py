import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand
from core.models import Person

logger = logging.getLogger(__name__)


def update_persons_phone():
    logger.info("FIXING PERSON'S PHONE..")
    persons = Person.objects.all()

    person_balance_update_count = 0

    for person in tqdm(persons):
        try:
            if person.phone[:1] == '0':
                person.phone = person.phone[1:]
                person.save()
                person_balance_update_count += 1

        except (AttributeError, IndexError, EOFError, IOError) as exception:
            logger.exception(exception)

    logger.info("{} Person's Phone Fixed.".format(person_balance_update_count))
    return True


class Command(BaseCommand):
    def handle(self, **options):
        update_persons_phone()
