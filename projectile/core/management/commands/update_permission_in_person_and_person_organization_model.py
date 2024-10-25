import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db.models import Count

from common.healthos_helpers import HealthOSHelper
from common.helpers import populate_es_index

from core.models import Person, PersonOrganization

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Update Person and Person Organization permission")

        # Get the organization ID using HealthOSHelper
        healthos_organization_id = HealthOSHelper().organization_id()

        # Query PersonOrganizations related to the specified organization and annotate with permission count
        person_organizations = PersonOrganization.objects.filter(
            organization_id=healthos_organization_id
        ).annotate(permission_count=Count('group_permission__id'))

        # Exclude PersonOrganizations with no permissions
        person_organizations = person_organizations.exclude(permission_count=0)

        person_list = []
        person_organization_list = []

        person_ids = []
        person_organization_ids = []

        # Iterate over filtered PersonOrganizations
        for person_organization in tqdm(person_organizations):

            person_ids.append(person_organization.person_id)
            person_organization_ids.append(person_organization.id)

            # Query related permissions and extract permission names
            permissions_queryset = person_organization.group_permission.all().values("permission__name")
            permission_names = [item["permission__name"] for item in permissions_queryset]

            # Sort the permission names alphabetically
            permission_names.sort()

            # Create a comma-separated string of permission names
            comma_separated_string = ", ".join(permission_names)

            # Create Person and PersonOrganization instances with updated permissions
            person_list.append(
                Person(
                    id=person_organization.person_id,
                    permissions=comma_separated_string
                )
            )
            person_organization_list.append(
                PersonOrganization(
                    id=person_organization.id,
                    permissions=comma_separated_string
                )
            )

        # Bulk update Person objects with updated permissions
        Person.objects.bulk_update(
            person_list, ["permissions"]
        )

        # Bulk update PersonOrganization objects with updated permissions
        PersonOrganization.objects.bulk_update(
            person_organization_list, ["permissions"]
        )

        # update Person and Person Organization elastic search model
        populate_es_index(
            'core.models.PersonOrganization',
            {'id__in': person_organization_ids},
        )
        populate_es_index(
            'core.models.Person',
            {'id__in': person_ids},
        )

        logger.info(f'Successfully updated total {person_organizations.count()}, Person and Person Organization '
                    f'permission')
