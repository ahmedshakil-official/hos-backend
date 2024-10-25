import json
import os
import logging

from tqdm import tqdm
from django.db import IntegrityError
from django.db.models import Q
from django.core.management.base import BaseCommand
from core.models import Organization
from projectile.settings import REPO_DIR

logger = logging.getLogger(__name__)


def get_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None


def restore_organization():
    print "IMPORTING ORGANIZATION"
    try:
        # the direcotry of json file
        data = open(os.path.join(REPO_DIR, 'tmp/organization.json'), 'r')
        json_data = json.load(data)
        organization_count = 0
        for d in tqdm(json_data):
            try:
                try:
                    Organization.objects.get(
                        Q(name=d['name']),
                        Q(primary_mobile=d['primary_mobile'])
                    )
                except Organization.DoesNotExist:
                    organization = Organization.objects.create(
                        pk=2,
                        name=d['name'],
                        slogan=d['slogan'],
                        address=d['address'],
                        primary_mobile=d['primary_mobile'],
                        other_contact=d['other_contact'],
                        contact_person=d['contact_person'],
                        contact_person_designation=d['contact_person_designation'],
                        email=d['email'],
                        website=d['website'],
                        domain=d['domain'],
                        type=0,

                    )
                    organization.save()
                    organization_count += 1
            except IntegrityError, e:
                logger.exception(e)
                logger.info(d)

    except Exception, e:
        logger.exception(e)

    return True


class Command(BaseCommand):
    def handle(self, **options):
        flag = restore_organization()
