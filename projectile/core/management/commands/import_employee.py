import json
import os
import logging

from tqdm import tqdm
from django.db import IntegrityError
from django.db.models import Q
from django.core.management.base import BaseCommand
from core.models import Person, Organization, Department, EmployeeDesignation
from projectile.settings import REPO_DIR

logger = logging.getLogger(__name__)


def get_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None


def restore_department():
    print "IMPORTING DEPARTMENT"
    try:
        # the direcotry of json file
        data = open(os.path.join(REPO_DIR, 'tmp/department.json'), 'r')
        json_data = json.load(data)
        department_count = 0
        for d in tqdm(json_data):
            try:
                try:
                    Department.objects.get(
                        Q(name=d['name']),
                        Q(is_global=1) | Q(organization=d['organization'])
                    )
                except Department.DoesNotExist:
                    department = Department.objects.create(
                        name=d['name'],
                        description=d['description'],
                        is_global=d['is_global'],
                        organization=Organization.objects.get(
                            pk=d['organization'])
                        # status =d['status']
                    )
                    department.save()
                    department_count += 1
            except IntegrityError, e:
                logger.exception(e)
                logger.info(d)

    except Exception, e:
        logger.exception(e)

    return True


def restore_designation():
    print "IMPORTING DESIGNATION"
    try:
        # the direcotry of json file
        data = open(os.path.join(REPO_DIR, 'tmp/designation.json'), 'r')
        json_data = json.load(data)
        designation_count = 0
        for d in tqdm(json_data):

            try:

                try:
                    EmployeeDesignation.objects.get(
                        name=d['name'],
                        department=Department.objects.get(
                            organization=d['organization'], name=d['department'])
                    )
                except EmployeeDesignation.DoesNotExist:
                    designation = EmployeeDesignation.objects.create(
                        name=d['name'],
                        description=d['description'],
                        is_global=d['is_global'],
                        department=Department.objects.get(
                            organization=d['organization'], name=d['department'])
                        # status =d['status']
                    )
                    designation.save()
                    designation_count += 1

            except IntegrityError, e:
                logger.exception(e)
                logger.info(d)

    except Exception, e:
        logger.exception(e)

    return True


def restore_employee():
    print "IMPORTING EMPLOYEE"
    try:
        data = open(os.path.join(REPO_DIR, 'tmp/employee.json'), 'r')
        json_data = json.load(data)
        person_count = 0
        for d in tqdm(json_data):
            try:

                try:
                    Person.objects.get(
                        first_name=d['first_name'],
                        last_name=d['last_name'],
                        phone=d['phone'],
                        dob=d['dob']
                    )
                except Person.DoesNotExist:
                    person = Person.objects.create(
                        mothers_name=d['mothers_name'],
                        husbands_name=d['husbands_name'],
                        last_name=d['last_name'],
                        permanent_address=d['permanent_address'],
                        present_address=d['present_address'],
                        first_name=d['first_name'],
                        person_group=1,
                        birth_id=d['birth_id'],
                        nid=d['nid'],
                        phone=d['phone'],
                        dob=d['dob'],
                        country=d['country'],
                        email=d['email'],
                        fathers_name=d['fathers_name'],
                        gender=d['gender'],
                        balance=d['balance'],
                        remarks=d['remarks'],
                        organization=Organization.objects.get(
                            pk=d['organization']),
                        designation=EmployeeDesignation.objects.get(department__organization=d['organization'],
                                                                    department__name=d['department'],
                                                                    name=d['designation'])
                    )
                    person.is_superuser = False
                    person.is_staff = True
                    person.set_password('87654321')
                    person.save()
                    person_count += 1

            except IntegrityError, e:
                logger.exception(e)
                logger.info(d)

    except Exception, e:
        logger.exception(e)


class Command(BaseCommand):
    def handle(self, **options):
        flag = restore_department()
        flag = restore_designation()
        flag = restore_employee()
