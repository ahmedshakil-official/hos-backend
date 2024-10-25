import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.core.cache import cache

from core.models import Person, PersonOrganization, PersonOrganizationGroupPermission
from common.enums import Status
from common.helpers import query_yes_no
from common.healthos_helpers import HealthOSHelper

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def delete_permission_cache(self, person_id_list):
        cache_keys = [f"permission_{str(person_id).zfill(7)}*" for person_id in person_id_list]
        for cache_key in cache_keys:
            cache.delete_pattern(cache_key, itersize=10000)

    def get_all_healthos_users_po_id(self):
        """
        Returns all users who are healthos users
        """
        person_organizations = PersonOrganization().get_all_non_inactives().filter(
            organization__id=HealthOSHelper().organization_id()
        )
        person_organization_id_list = list(person_organizations.values_list("pk", flat=True))
        person_id_list = list(person_organizations.values_list("person_id", flat=True))
        return person_organization_id_list, person_id_list

    def remove_all_permissions(self):
        person_organization_id_list, person_id_list = self.get_all_healthos_users_po_id()
        person_organization_permissions = PersonOrganizationGroupPermission.objects.filter(
            person_organization__id__in=person_organization_id_list
        ).only('id')
        # Delete permissions
        person_organization_permissions._raw_delete(person_organization_permissions.db)
        self.delete_permission_cache(person_id_list)

    def handle(self, **options):
        question = "This script will remove all permissions of HealthOS users, All the Lighthouse and Procurement users will be affected."
        if query_yes_no(question, "no"):
            logger.info("Removing all permissions")
            self.remove_all_permissions()
            logger.info("Done!!!")
        else:
            logger.info("Aborting")
