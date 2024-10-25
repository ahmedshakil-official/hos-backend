import logging

from tqdm import tqdm
from django.db import IntegrityError
from django.core.management.base import BaseCommand
from core.models import Organization, PersonOrganization

logger = logging.getLogger(__name__)


def fix_organization():

    gdc = Organization.objects.get(pk=1)

    gdc_patients = PersonOrganization.objects.filter(organization=gdc)

    for patient in tqdm(gdc_patients):
        patient.person_group = patient.person.person_group
        patient.save()

class Command(BaseCommand):
    def handle(self, **options):
        flag = fix_organization()
