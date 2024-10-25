import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

from core.models import Organization, Area

logger = logging.getLogger(__name__)


def expire_organizations_cache(area_ids):
    # Fetch all non-inactive organizations based on area_ids
    organizations = Organization().get_all_non_inactives().filter(area_id__in=area_ids)
    # Iter through each organization and expire its cache
    for organization in tqdm(organizations):
        try:
            # Expire the cache for the current organization
            organization.expire_cache()
        except AttributeError:
            # Log a warning if the id is not found in the object
            logger.warning("Invalid Organization id")
        except Exception as e:
            logger.warning(e)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Start: Populate area in Organization model based on delivery_thana field.")

        # Get all non-inactive areas
        areas = Area().get_all_non_inactives().only("id", "code")

        # Iterate through areas and update corresponding organizations
        for area in tqdm(areas, colour="GREEN"):

            # Retrieve all non-inactive organizations with a specific delivery_thana code
            # and update their area_id to the corresponding area's id
            Organization().get_all_non_inactives().filter(
                delivery_thana=area.code
            ).update(area_id=area.id)

        logger.info("End: Successfully populated area field in Organization model based on delivery_thana.")

        logger.info("Start: Expiring Organizations Cache Started")
        area_ids = areas.values_list("id", flat=True)
        # Call the helper method to clear the cache.
        expire_organizations_cache(area_ids)

        logger.info("End: Expiring Organizations cache Successfull!!!")
