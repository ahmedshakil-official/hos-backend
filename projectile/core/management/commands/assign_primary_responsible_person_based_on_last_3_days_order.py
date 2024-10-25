import logging, os

from tqdm import tqdm
from datetime import date
from itertools import groupby
from django.core.management.base import BaseCommand
from core.models import Organization

logger = logging.getLogger(__name__)


def all_equal(iterable):
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def update_organization_responsible_employee(organization_id):
    from common.helpers import custom_elastic_rebuild
    from core.models import Organization
    from pharmacy.models import Purchase
    from pharmacy.enums import OrderTrackingStatus

    distributor_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
    orders = Purchase.objects.filter(
        organization__id=organization_id,
        distributor__id=distributor_id,
        responsible_employee__isnull=False,
        tentative_delivery_date__isnull=False,
        tentative_delivery_date__lt=date.today()
    ).exclude(
        current_order_status__in=[
            OrderTrackingStatus.REJECTED,
            OrderTrackingStatus.CANCELLED
        ]
    ).only('tentative_delivery_date', 'responsible_employee')

    delivery_dates = orders.values(
        'tentative_delivery_date'
    ).order_by('-tentative_delivery_date').distinct('tentative_delivery_date')[0:3]
    delivery_date_list = list(map(lambda item: item['tentative_delivery_date'], list(delivery_dates)))

    if len(delivery_date_list) == 3:

        responsible_employee_list = orders.filter(
            tentative_delivery_date__in=delivery_date_list
        ).values_list('responsible_employee__id', flat=True)

        # Update primary responsible employee if all orders(delivery_date_list) are assigned to same employee
        if all_equal(list(responsible_employee_list)):
            responsible_employee_id = responsible_employee_list[0]
            organization_instance = Organization.objects.only('primary_responsible_person_id').filter(pk=organization_id)
            organization_instance.update(primary_responsible_person_id=responsible_employee_id)
            custom_elastic_rebuild(
                'core.models.Organization',
                {'id': organization_id}
            )
            logger.info(
                f"Updated primary responsible employee id {responsible_employee_id} for organization {organization_id}"
            )


def assign_primary_responsible_person():
    logger.info('Assigning Primary Responsible Person Based on Last 3 Days Order')
    organizations = Organization().get_all_actives().values_list('pk', flat=True)
    for organization_id in list(organizations):
        update_organization_responsible_employee(
            organization_id
        )

class Command(BaseCommand):
    def handle(self, **options):
        assign_primary_responsible_person()
