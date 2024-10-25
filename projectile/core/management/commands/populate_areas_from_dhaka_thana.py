import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

from core.enums import DhakaThana
from core.models import Area

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Start: Populating Areas from DhakaThana enum")

        # Create a list to store Area objects
        create_areas = []

        # Iterate through DhakaThana enum choices to create Area objects
        for thana_code, thana_name in tqdm(DhakaThana().choices(), colour="GREEN"):

            # if any Dhaka thana has code 0, then skip the thana
            if thana_code != 0:
                area = Area().get_all_non_inactives().filter(code=thana_code).only("id")

                # If any area already exists with any thana code, skip it
                if not area.exists():
                    create_areas.append(
                        Area(
                            name=thana_name,
                            code=thana_code
                        )
                    )

        # Bulk create the Area objects in the database
        Area.objects.bulk_create(create_areas)

        logger.info("End: Populating Areas from DhakaThana enum")
