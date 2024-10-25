import json
import os
import logging

from tqdm import tqdm
from django.db import IntegrityError
from django.db.models import Q
from django.core.management.base import BaseCommand
from core.models import GroupPermission
from projectile.settings import REPO_DIR

logger = logging.getLogger(__name__)


def restore_group_permission():
    logger.info("IMPORTING GROUP PERMISSIONS")
    try:
        # the direcotry of json file
        data = open(os.path.join(REPO_DIR, 'tmp/group_permission.json'), 'r')
        json_data = json.load(data)
        group_permission_count = 0
        for item in tqdm(json_data):
            try:
                try:
                    GroupPermission.objects.get(
                        Q(name=item['name']))
                except GroupPermission.DoesNotExist:
                    group_permission = GroupPermission.objects.create(
                        name=item['name'])

                    group_permission.save()
                    group_permission_count += 1

            except IntegrityError as exception:
                logger.exception(exception)
                logger.info(item)
                logger.info("{} GroupPermission created".format(group_permission_count))
        logger.info("{} GroupPermission created".format(group_permission_count))

    except (IntegrityError, IndexError, EOFError, IOError) as exception:
        logger.exception(exception)

    return True


class Command(BaseCommand):
    def handle(self, **options):
        flag = restore_group_permission()
