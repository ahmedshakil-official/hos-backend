import logging

from django.core.management.base import BaseCommand
from django.db.models import Count, CharField, Q, F, Value
from django.db.models.functions import Concat

from core.models import Organization


logger = logging.getLogger(__name__)


def update_organizations_duplicate_locations():
    # Annotate the location field by concatenating latitude and longitude
    organizations_with_same_locations = (
        Organization.objects.exclude(
            Q(geo_location__isnull=True) | Q(geo_location={}),
        )
        .annotate(
            location=Concat(
                F("geo_location__currentPosition__latitude"),
                Value(" "),
                F("geo_location__currentPosition__longitude"),
                output_field=CharField(),
            )
        )
        .values("location")
        .annotate(num_organizations=Count("id"))
        .filter(num_organizations__gt=2)
    )

    # Retrieve the organization IDs for organizations that have the same location
    organizations_with_same_location_ids = (
        Organization.objects.exclude(
            Q(geo_location__isnull=True) | Q(geo_location={}),
        )
        .annotate(
            location=Concat(
                F("geo_location__currentPosition__latitude"),
                Value(" "),
                F("geo_location__currentPosition__longitude"),
                output_field=CharField(),
            )
        )
        .filter(location__in=organizations_with_same_locations.values("location"))
        .values_list("id", flat=True)
    )

    # update the geo_location to {}
    Organization.objects.filter(id__in=organizations_with_same_location_ids).update(
        geo_location={}
    )


class Command(BaseCommand):
    help = "Set geo_location to {} for Organizations with non-unique geo_location."

    def handle(self, *args, **kwargs):
        logger.info(
            "update geo_location of organizations if geo_location is duplicate."
        )

        # Call the function to set location {} if they are same
        update_organizations_duplicate_locations()

        logger.info(
            "Removed geo_location of organizations with duplicate geo_location Success."
        )
