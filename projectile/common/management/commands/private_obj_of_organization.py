import logging

from common.enums import Status, PublishStatus

logger = logging.getLogger('')


def get_private_obj_of_organization(ClassOfObject, attribute=None):

    return ClassOfObject.objects.filter(
        **attribute
    )


def make_obj_global(obj):
    try:
        obj.is_global = PublishStatus.INITIALLY_GLOBAL
        obj.organization = None
        obj.save()
    except (AssertionError, NameError):
        logger.error("Failed to operate on {}".format(obj))
