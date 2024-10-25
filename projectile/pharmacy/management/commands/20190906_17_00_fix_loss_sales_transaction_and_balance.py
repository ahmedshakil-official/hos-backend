import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db.models import Q, F, Sum

from account.models import Transaction, Accounts
from common.enums import Status
from common.helpers import custom_elastic_rebuild, custom_elastic_delete
from core.models import PersonOrganization
from pharmacy.models import Sales

logger = logging.getLogger(__name__)


def is_accepted(msg):
    try:
        logger.info(msg)
        used_before = raw_input("DO YOU WANT TO CONTINUE? (Yes/No): ")
        if used_before in ['yes', 'Yes']:
            return True
        if used_before in ['no', 'No']:
            return False
        else:
            return is_accepted(msg)
    except NameError:
        return is_accepted(msg)

def fix_transaction_and_accounts_balance():
    logger.info("Populating Transaction Data")
    transaction = Transaction.objects.filter(
        status=Status.ACTIVE,
        sales__isnull=False,
        sales__status=Status.LOSS,
    )
    transaction_by_accounts = transaction.values(
        'accounts'
    ).order_by('accounts').annotate(total_amount=Sum('amount'))
    accounts = []
    for account in tqdm(transaction_by_accounts):
        instance = Accounts.objects.filter(id=account['accounts'])
        instance.update(balance=instance[0].balance - account['total_amount'])
        accounts.append(account['accounts'])
    # update search documents of transactions
    if len(accounts) > 0:
        custom_elastic_rebuild(
            'account.models.Accounts',
            {'id__in': accounts}
        )

    transaction_ids = list(transaction.values_list('id', flat=True))
    transaction.update(status=Status.INACTIVE)
    # update search documents of transactions
    for id_ in transaction_ids:
        custom_elastic_delete('account.models.Transaction', id_)

    logger.info("{} transaction and account balance updated".format(
        transaction_by_accounts.count()))

def fix_buyer_balance():
    logger.info("Populating Sales Data")
    accept = is_accepted("NOW BUYER\'S BALANCE WILL BE UPDATED "\
        "(THIS PROCESS WON'T BE REVERTED AGAIN)!!!!!!!")
    if accept:
        sales = Sales.objects.filter(
            status=Status.LOSS,
            person_organization_buyer__isnull=False,
        ).values(
            'person_organization_buyer'
        ).order_by(
            'person_organization_buyer'
        ).annotate(
            total_amount=Sum('amount') - Sum('discount') + Sum('round_discount') + Sum('vat_total'),
            paid_amount=F('paid_amount'),
        )
        buyers = []
        for sale in tqdm(sales):
            if sale['total_amount'] - sale['paid_amount'] > 0:
                instance = PersonOrganization.objects.filter(
                    id=sale['person_organization_buyer']
                )
                instance.update(
                    balance=instance[0].balance - (sale['total_amount'] - sale['paid_amount']))
                buyers.append(sale['person_organization_buyer'])
        # update loss sales paid_amount to 0
        Sales.objects.filter(status=Status.LOSS, paid_amount__gt=0).update(paid_amount=0)
        # update search documents of Buyer instances
        custom_elastic_rebuild(
            'core.models.PersonOrganization',
            {'id__in': buyers}
        )
        logger.info("{} buyer\'s balance updated".format(len(buyers)))


class Command(BaseCommand):
    '''
    This management script to Fix incorrect time zone of Sales and Purchase
    '''
    def handle(self, **options):
        msg = "IF THIS SCRIPT RUNS MORE THEN 1 TIME, BUYER BALANCE WILL BE MIS-MATCH"
        if is_accepted(msg):
            fix_transaction_and_accounts_balance()
            fix_buyer_balance()
        else:
            logger.info(
                "Transaction, Accounts, Buyer balance updated previously")
