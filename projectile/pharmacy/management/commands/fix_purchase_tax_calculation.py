import logging

from tqdm import tqdm
from django.core.management.base import BaseCommand
from ...models import Purchase

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-suppliers-too',
            action='store_true',
            dest='fix_suppliers',
            default=False,
            help='Fix Suppliers too',
        )

    def handle(self, *args, **options):
        # loop through the whole purchase entries
        for instance in tqdm(Purchase.objects.all()):
            #
            if instance.grand_total == 0:
                # calculate vat_total
                instance.vat_total = round(instance.amount * instance.vat_rate / 100, 2)
                # calculate tax_total
                instance.tax_total = round(instance.amount * instance.tax_rate / 100, 2)

                # calculate grand_total
                instance.grand_total = round(
                    instance.amount +
                    instance.vat_total +
                    instance.tax_total -
                    instance.discount,
                    2
                )
                # save the instance
                instance.save()

                # only if passed from shell
                if options['fix_suppliers']:
                    # revert previous applied
                    instance.supplier.balance -= instance.transport - instance.discount

                    # calculate the supplier balance
                    instance.supplier.balance += instance.grand_total + instance.transport - instance.discount
                    # and update the supplier balance
                    instance.supplier.save()