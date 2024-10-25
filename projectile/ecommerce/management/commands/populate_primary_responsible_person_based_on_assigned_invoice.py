import os
import logging
from typing import Any, Optional
from tqdm import tqdm

from django.core.management.base import BaseCommand

from common.helpers import populate_es_index
from common.enums import Status

from ecommerce.models import OrderInvoiceGroup

from core.models import PersonOrganization, Organization
from core.enums import PersonGroupType

from pharmacy.enums import OrderTrackingStatus

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command for populating primary responsible person for
    specific organizations based on their last assigned invoice groups.
    """

    help = "Set primary_responsible_person for organizations based on last assigned invoice groups"

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        porter_codes = [
            "P0350",
            "P0351",
            "P0352",
            "P0353",
            "P0354",
            "P0355",
            "P0356",
            "P0357",
            "P0358",
            "P0359",
        ]
        distributor_id = os.environ.get("DISTRIBUTOR_ORG_ID", 303)

        person_organizations = PersonOrganization.objects.filter(
            code__in=porter_codes,
            organization__id=distributor_id,
            person_group=PersonGroupType.EMPLOYEE,
            status__in=[Status.ACTIVE, Status.DRAFT],
        ).values_list("id", flat=True)

        for person_organization in tqdm(list(person_organizations)):
            organization_pk_list = list(OrderInvoiceGroup.objects.filter(
                responsible_employee__id=person_organization
            ).exclude(
                current_order_status__in=[
                    OrderTrackingStatus.CANCELLED,
                    OrderTrackingStatus.REJECTED,
                ]
            ).values_list("order_by_organization", flat=True))

            # Update primary responsible employee
            Organization.objects.filter(
                pk__in=organization_pk_list
            ).update(
                primary_responsible_person_id=person_organization
            )
            # Update ES document
            populate_es_index(
                "core.models.Organization",
                {"pk__in": organization_pk_list},
                cli=True
            )

        logger.info("Done!!")
