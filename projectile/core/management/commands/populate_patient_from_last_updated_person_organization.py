import logging
from django.core.management.base import BaseCommand
from tqdm import tqdm
from core.models import PersonOrganization, Person

from common.enums import Status


logger = logging.getLogger(__name__)


def update_person_attribute(person_organization, attributes):
    # will traverse through all atributes email, phone etc
    for attribute in attributes:
        # get PersonOrganization.email, PersonOrganization.phone on each travarse

        if (hasattr(person_organization, attribute) and
                hasattr(person_organization.person, attribute)):
            attribute_value = getattr(person_organization, attribute)

            # Check if this attribute on PersonOrganization is not None
            if attribute_value is not None:

                # Set value on Person
                setattr(person_organization.person, attribute, attribute_value)

    person_organization.person.save()


def populate_patient_from_person_organization():
    '''
    This function will take all record of last updated PersonOrganization, then update
    the person instance
    '''
    person_list = Person.objects.filter(status=Status.ACTIVE)

    for person_item in tqdm(person_list):
        person_organization = PersonOrganization.objects.filter(
            person=person_item
        ).order_by('-updated_at')[0]
        update_person_attribute(
            person_organization,
            [
                'email', 'phone', 'person_group', 'first_name', 'last_name',
                'country', 'language', 'economic_status', 'permanent_address',
                'present_address', 'dob', 'family', 'gender', 'relatives_name',
                'relatives_address', 'relatives_contact_number', 'relatives_relation',
                'family_relation', 'patient_refered_by', 'designation', 'joining_date',
                'registration_number', 'degree', 'remarks', 'medical_remarks',
                'company_name', 'is_positive'
            ]
        )


class Command(BaseCommand):
    def handle(self, **options):
        populate_patient_from_person_organization()
