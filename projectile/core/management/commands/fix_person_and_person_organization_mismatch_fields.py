import logging, os

from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.core.cache import cache
from common.cache_keys import (
    USER_PROFILE_DETAILS_CACHE_KEY_PREFIX,
)
from core.models import Person, PersonOrganization

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, **options):
        logger.info("FIXING PERSON AND PERSON ORGANIZATION MISMATCH FIELDS FOR HEALTHOS")
        person_organizations = PersonOrganization.objects.filter(
            person__isnull=False,
            organization__id=os.environ.get('DISTRIBUTOR_ORG_ID', 303)
        ).values(
            'id',
            'person_id',
            'email', 'phone', 'first_name', 'last_name', 'code', 'language', 'nid', 'dob',
            'present_address', 'permanent_address',
            'balance', 'opening_balance',
            'contact_person', 'contact_person_number', 'contact_person_address',
            'degree', 'registration_number', 'joining_date', 'designation_id', 'person_group'
        )

        obj_to_update = []
        cache_keys_to_be_delete = []
        for person_organization in tqdm(person_organizations):
            # Update all fields in values in person model
            obj_to_update.append(
                Person(
                    id=person_organization['person_id'],
                    email=person_organization['email'],
                    phone=person_organization['phone'],
                    first_name=person_organization['first_name'],
                    last_name=person_organization['last_name'],
                    code=person_organization['code'],
                    language=person_organization['language'],
                    nid=person_organization['nid'],
                    dob=person_organization['dob'],
                    present_address=person_organization['present_address'],
                    permanent_address=person_organization['permanent_address'],
                    balance=person_organization['balance'],
                    opening_balance=person_organization['opening_balance'],
                    contact_person=person_organization['contact_person'],
                    contact_person_number=person_organization['contact_person_number'],
                    contact_person_address=person_organization['contact_person_address'],
                    degree=person_organization['degree'],
                    registration_number=person_organization['registration_number'],
                    joining_date=person_organization['joining_date'],
                    designation_id=person_organization['designation_id'],
                    person_group=person_organization['person_group']
                )
            )
            cache_keys_to_be_delete.append(
                f"{USER_PROFILE_DETAILS_CACHE_KEY_PREFIX}{person_organization['person_id']}"
            )

        Person.objects.bulk_update(
            obj_to_update,
            [
                'email', 'phone', 'first_name', 'last_name', 'code',
                'present_address', 'permanent_address',
                'language', 'nid', 'dob', 'balance', 'opening_balance', 'contact_person',
                'contact_person_number', 'contact_person_address', 'degree', 'registration_number',
                'joining_date', 'designation_id', 'person_group'
            ],
            batch_size=1000
        )
        cache.delete_many(cache_keys_to_be_delete)
        logger.info("FIXED PERSON AND PERSON ORGANIZATION MISMATCH FIELDS!!!")
