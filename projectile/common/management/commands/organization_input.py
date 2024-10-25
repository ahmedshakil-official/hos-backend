import logging
from common.enums import Status
from core.models import Organization

logger = logging.getLogger('')


def take_input():
    organization_id = input("Choose a correct organization id(0 to exit): ")
    return organization_id


def get_organization_input():

    organization = None
    organizations = Organization.objects.filter(
        status=Status.ACTIVE
    )

    logger.info("***********************************************************")
    logger.info("ID ----- NAME")

    for item in organizations:
        logger.info("{}       {}".format(item.id, item.name))

    logger.info("***********************************************************")

    organization_id = take_input()

    while True:
        try:
            if organization_id == 0:
                return None
            organization = Organization.objects.get(id=organization_id)
            if organization:
                return organization
            else:
                continue
        except Organization.DoesNotExist:
            organization_id = take_input()
    return None
