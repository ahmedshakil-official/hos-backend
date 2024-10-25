import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from common.enums import Status, PublishStatus
from core.models import Organization
from pharmacy.models import Product

logger = logging.getLogger('')


def take_organization_input():
    organization_id = input("Choose a correct organization id(0 to exit): ")
    return organization_id


def move_all_global_products():
    organizations = Organization.objects.filter(status=Status.ACTIVE)
    logger.info("***********************************************************")
    logger.info("ID ----- NAME")
    for organization in organizations:
        logger.info("{}       {}".format(organization.id, organization.name))

    logger.info("***********************************************************")
    organization_id = take_organization_input()

    while True:
        try:
            if organization_id == 0:
                return
            organization = Organization.objects.get(id=organization_id)
            if organization:
                break
            else:
                continue
        except Organization.DoesNotExist:
            organization_id = take_organization_input()

    products = Product.objects.filter(
        status=Status.ACTIVE,
        is_global__in=[
            PublishStatus.INITIALLY_GLOBAL,
            PublishStatus.WAS_PRIVATE_NOW_GLOBAL
        ],
    )

    count = 0
    for product in tqdm(products):
        try:
            product.organization = organization
            product.is_global = PublishStatus.PRIVATE
            product.save()
            count += 1
        except (IntegrityError, AttributeError, IOError) as exception:
            logger.exception(exception)

    logger.info("{} products assigned into {}".format(
        count, organization.name))


class Command(BaseCommand):
    def handle(self, **options):
        move_all_global_products()
