import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand

from core.models import Person, PersonOrganization, Organization
from common.enums import Status

logger = logging.getLogger(__name__)


def get_organization(organization_name):
    '''
    return organization with given name
    '''
    try:
        return Organization.objects.get(
            name=organization_name,
            status=Status.ACTIVE
        )
    except Organization.DoesNotExist:
        return None


def update_code(dataset, look_for, update_to):
    '''
    check if any person of given dataset contain value in look_for, in his code, if s/he does
    then update it with value given in update_to
    '''
    for person in tqdm(dataset):
        if person.code is not None and look_for in person.code:
            person.code = person.code.replace(look_for, update_to, 1)
            person.save()


def update_persons_code():
    '''
    this function will serach on Person, PersonOrganization model for data of
    GDC, and will replace person code OMIS with GDC
    '''

    logger.info("FIXING PATIENT CODE..")

    gdc = get_organization('Gonoshasthaya Dialysis Center')

    look_for = "OMIS"
    update_to = "GDC"

    if gdc is not None:
        persons = Person.objects.filter(
            organization=gdc,
            status=Status.ACTIVE
        )
        person_on_organiztion = PersonOrganization.objects.filter(
            organization=gdc,
            status=Status.ACTIVE
        )

        logger.info("FIXING PERSON CODE..")
        update_code(persons, look_for, update_to)

        logger.info("FIXING PERSON ORGANIZATION CODE..")
        update_code(person_on_organiztion, look_for, update_to)


class Command(BaseCommand):
    def handle(self, **options):
        update_persons_code()
