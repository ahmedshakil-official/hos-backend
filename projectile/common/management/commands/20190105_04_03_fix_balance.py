import logging

from django.core.management.base import BaseCommand
from django.db.models import Sum

from account.models import (
    Transaction,
    Accounts,
)

from common.helpers import (
    get_organization_by_input_id,
    get_account_by_input_id,
)

from common.enums import Status

logger = logging.getLogger()


class Command(BaseCommand):
    '''
    This management script will fix accounts balance
    '''

    def handle(self, **options):

        organization_instance = get_organization_by_input_id()

        accounts_to_fix = get_account_by_input_id(
            organization_instance, 'select a/c to fix : ')

        transaction_amount = Transaction.objects.filter(
            organization=organization_instance,
            status=Status.ACTIVE,
            accounts=accounts_to_fix
        ).aggregate(Sum('amount'))

        accounts_to_fix.balance = transaction_amount['amount__sum'] + \
            accounts_to_fix.opening_balance
        accounts_to_fix.save()
