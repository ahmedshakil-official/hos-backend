import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand
from core.models import PersonOrganization


logger = logging.getLogger(__name__)


def update_person_organization_attribute(obj, attributes):
    # will traverse through all atributes email, phone etc
    for attribute in attributes:
        # get PersonOrganization.person.email, PersonOrganization.person.phone on each travarse
        attribute_value = getattr(obj.person, attribute)

        # Check if this attribute on Person is not None
        if attribute_value is not None:

            # Set value on PersonOrganization
            setattr(obj, attribute, attribute_value)

    obj.save()


def populate_patient_organization():
    '''
    This function will take all record of PersonOrganization, fetch each records details
    from Person model and then store those information on PersonOrganization
    '''

    person_list = PersonOrganization.objects.all()
    for person in tqdm(person_list):
        update_person_organization_attribute(
            person,
            [
                'email', 'phone', 'code', 'person_group', 'first_name', 'last_name', 'country', 'language',
                'economic_status', 'permanent_address', 'present_address', 'dob', 'family', 'gender',
                'relatives_name', 'relatives_address', 'relatives_contact_number', 'relatives_relation',
                'family_relation', 'patient_refered_by', 'designation', 'joining_date', 'registration_number',
                'degree', 'remarks', 'medical_remarks', 'company_name', 'is_positive',
                'nid', 'profile_image', 'hero_image', 'birth_id', 'mothers_name', 'fathers_name', 'husbands_name',
                'fingerprint_1', 'fingerprint_2', 'fingerprint_3'

            ]
        )
    return True


class Command(BaseCommand):
    def handle(self, **options):
        flag = populate_patient_organization()
