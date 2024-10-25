import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand

from common.helpers import (
    get_organization_by_input_id,
)
from common.enums import Status
from core.models import Person, PersonOrganization, Organization

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        logger.info("Changing patient code prefix.")

        # Taking input for an organization
        organization_instance = get_organization_by_input_id()
        new_prefix = input("Enter New Patient Code Prefix : ")
        if not new_prefix:
            logger.info("New Prefix Can't be Blank.")
            return
        try:
            settings = organization_instance.get_settings_instance()
            old_prefix = settings.patient_code_prefix or ""
            person_organizations = PersonOrganization().get_active_from_organization(
                organization_instance).filter(code__isnull=False)
            for person_organization in tqdm(person_organizations):
                old_code = person_organization.code
                new_code = old_code.replace(old_prefix, new_prefix)
                old_person_code = person_organization.person.code if person_organization.person.code else ""
                new_person_code = old_person_code.replace(old_prefix, new_prefix)
                person_organization.code = new_code
                person_organization.person.code = new_person_code
                person_organization.save(update_fields=['code'])
                person_organization.person.save(update_fields=['code'])
                # Update prefix in settings
                settings.patient_code_prefix = new_prefix
                settings.save(update_fields=['patient_code_prefix'])
        except Exception as exp:
            logger.error("Error!! {}".format(str(exp)))
        logger.info("Done!")
