import logging
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db.models import Sum, FloatField, F, Q
from django.db.models.functions import Coalesce
from django.conf import settings

from common.enums import Status
from pharmacy.models import Purchase
from pharmacy.enums import DistributorOrderType, PurchaseType
from ecommerce.models import OrderInvoiceGroup

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, **options):
        logger.info("Fixing Order Invoice Group Responsible Person")

        if settings.DEBUG:
            distributor_org_id = 41
        else:
            distributor_org_id = 303

        order_filters = {
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER,
            "distributor__id": distributor_org_id,
            "invoice_group__isnull": False,
            "responsible_employee__isnull": False,
        }

        orders = Purchase.objects.filter(
            ~Q(invoice_group__responsible_employee__id=F('responsible_employee_id')),
            **order_filters,
        ).only(
            'invoice_group',
            'responsible_employee',
        )

        update_invoice_groups = []
        for order in tqdm(orders):
            for item in order.invoice_group.orders.all():
                if order.responsible_employee_id == item.responsible_employee_id:
                    valid = True
                else:
                    valid = False
                    break
            if valid:
                _invoice_group = order.invoice_group
                _invoice_group.responsible_employee_id = order.responsible_employee_id
                update_invoice_groups.append(_invoice_group)
            else:
                order_ids = list(order.invoice_group.orders.all().values_list('pk', flat=True))
                order_ids = ", ".join([str(item) for item in order_ids])
                logger.info(
                    f"{order.invoice_group.orders.all().count()} orders({order_ids}) of invoice group {order.invoice_group_id} have different responsible person"
                )
        OrderInvoiceGroup.objects.bulk_update(
            objs=update_invoice_groups,
            fields=['responsible_employee_id',],
            batch_size=100,
        )
