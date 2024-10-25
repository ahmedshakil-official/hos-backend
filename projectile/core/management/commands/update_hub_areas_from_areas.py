"""
Management script for copying hub areas from areas field.
"""
import os
import logging

from django.core.management.base import BaseCommand

from tqdm import tqdm

from core.models import DeliveryHub


logger = logging.getLogger(__name__)


def populate_hub_areas():
    # Get all actives delivery hubs
    delivery_hubs = DeliveryHub().get_all_actives()
    delivery_hubs_to_be_update = []
    for delivery_hub in tqdm(delivery_hubs):
        areas = delivery_hub.areas
        # Set hub_areas value from areas field
        delivery_hub.hub_areas = areas
        delivery_hubs_to_be_update.append(delivery_hub)

    # bulk update delivery hub areas
    DeliveryHub.objects.bulk_update(delivery_hubs_to_be_update, fields=["hub_areas"])


class Command(BaseCommand):
    """Django Command to populate hub areas from areas."""

    def handle(self, **options):
        """Entry point for command."""
        logger.info("Management script for populate hub areas started!")

        # Update delivery hub areas
        populate_hub_areas()

        logger.info("Hub areas population is Successfull!")
