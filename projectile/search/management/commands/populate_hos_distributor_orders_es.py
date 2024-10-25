import os
from elasticsearch_dsl import Index
from django.core.management.base import BaseCommand

from common.enums import Status
from common.helpers import populate_es_index
from pharmacy.enums import PurchaseType, DistributorOrderType
from search.document.pharmacy_search import PurchaseDocumentForOrder


class Command(BaseCommand):
    """
    This management script will populate all order of HealthOS
    """

    def handle(self, **options):
        org_id = os.environ.get("DISTRIBUTOR_ORG_ID", 303)
        org_id = org_id if org_id else 303
        order_doc = PurchaseDocumentForOrder()
        index_name = order_doc.Index.name
        index = Index(index_name)
        # Create index if not exists
        if not index.exists():
            index.create()
        filters = {
            "distributor_order_group__isnull": False,
            "tentative_delivery_date__range": ["2023-11-01", "2023-12-31"],
        }
        populate_es_index("pharmacy.models.Purchase", filters, True)
