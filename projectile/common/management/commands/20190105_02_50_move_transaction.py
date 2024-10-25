import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand

from account.models import Transaction

from common.helpers import (
    get_organization_by_input_id,
    get_date_input,
    get_employee_person_organization_by_input_id,
    get_account_by_input_id,
)

from common.enums import Status

logger = logging.getLogger()


class Command(BaseCommand):
    '''
    This management script will take input of an organization, accounts an employee and two date
    and move all transaction to another account
    '''

    def handle(self, **options):
        # logger.info("Populating Transaction Group")
        organization_instance = get_organization_by_input_id()
        employee = get_employee_person_organization_by_input_id(
            organization_instance, 'select employee : ')
        accounts_from = get_account_by_input_id(
            organization_instance, 'select a/c from : ')
        accounts_to = get_account_by_input_id(
            organization_instance, 'select a/c to : ')

        date_from = get_date_input('Give date From : ')
        date_to = get_date_input('Give date To : ')

        transactions = Transaction.objects.filter(
            organization=organization_instance,
            status=Status.ACTIVE,
            accounts=accounts_from,
            person_organization_received=employee,
            date__range=(date_from, date_to)
        )

        for item in tqdm(transactions):
            item.accounts=accounts_to
            item.save()
