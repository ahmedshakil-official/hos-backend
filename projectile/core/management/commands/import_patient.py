import json
import os
import logging

from tqdm import tqdm
from django.db import IntegrityError
from django.db.models import Q
from django.core.management.base import BaseCommand
from core.models import Person, Organization
from projectile.settings import REPO_DIR

logger = logging.getLogger(__name__)


def get_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None


class Command(BaseCommand):
    def handle(self, **options):
        print "IMPORTING PATIENT"
        try:
            data = open(os.path.join(REPO_DIR, 'tmp/patient.json'), 'r')
            json_data = json.load(data)
            person_count = 0
            for d in tqdm(json_data):

                try:
                    Person.objects.get(
                        Q(first_name=d['first_name']),
                        Q(phone=d['phone']),
                        Q(organization=d['organization'])
                    )
                except Person.DoesNotExist:

                    person = Person.objects.create(
                        code=d['code'],
                        mothers_name=d['mothers_name'],
                        husbands_name=d['husbands_name'],
                        last_name=d['last_name'],
                        permanent_address=d['permanent_address'],
                        present_address=d['present_address'],
                        relatives_contact_number=d['relatives_contact_number'],
                        first_name=d['first_name'],
                        person_group=0,
                        relatives_name=d['relatives_name'],
                        birth_id=d['birth_id'],
                        economic_status=d['economic_status'],
                        nid=d['nid'],
                        phone=d['phone'],
                        relatives_address=d['relatives_address'],
                        dob=d['dob'],
                        country=d['country'],
                        relatives_relation=d['relatives_relation'],

                        email=d['email'],
                        fathers_name=d['fathers_name'],
                        gender=d['gender'],
                        balance=d['balance'],
                        remarks=d['remarks'],
                        medical_remarks=d['medical_remarks'],
                        patient_refered_by=d['patient_refered_by'],
                        organization=Organization.objects.get(
                            pk=d['organization'])
                    )
                    person.is_superuser = False
                    person.is_staff = False
                    person.set_password('87654321')
                    person.save()
                    person_count += 1

                except IntegrityError, e:
                    logger.exception(e)
                    logger.info(d)

        except Exception, e:
            logger.exception(e)
