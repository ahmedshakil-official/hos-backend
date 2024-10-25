import logging
from tqdm import tqdm
import datetime

from django.core.management.base import BaseCommand

from core.models import PersonOrganization
from pharmacy.models import StockAdjustment

from common.enums import Status
from core.enums import PersonGroupType
from pharmacy.enums import DisbursementFor

logger = logging.getLogger(__name__)


def fix_adjustment():

    logger.info("Updating Stock Adjustment")
    employee_phone = ["1772717447", "1854034515"]

    start_date = datetime.datetime.strptime('01052018', "%d%m%Y").date()
    end_date = datetime.datetime.strptime('31052018', "%d%m%Y").date()

    employees = PersonOrganization.objects.filter(
        phone__in=employee_phone,
        status=Status.ACTIVE,
        person_group=PersonGroupType.EMPLOYEE
    ).only('id',)

    adjustments = StockAdjustment.objects.filter(
        is_product_disbrustment=False,
        person_organization_employee__in=employees,
        date__range=(start_date, end_date)
    ).order_by('date')

    for adjustment in tqdm(adjustments):
        adjustment.is_product_disbrustment = True
        adjustment.disbursement_for = DisbursementFor.PATIENT
        adjustment.save()


class Command(BaseCommand):
    def handle(self, **options):
        fix_adjustment()
