import logging

from django.core.management.base import BaseCommand

from elasticsearch_dsl import Index

from common.helpers import query_yes_no
from search.document.pharmacy_search import PurchaseDocumentForOrder

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Index data from PurchaseDocumentForOrder into Elasticsearch'

    def handle(self, *args, **options):
        purchase_document = PurchaseDocumentForOrder()
        index_name = purchase_document.Index.name
        index = Index(index_name)

        input_text = "Are you sure you want to delete the 'hos_ecom_pharmacy_purchase_orders' index? "

        if query_yes_no(question=input_text):
            logger.info("Deleting index 'hos_ecom_pharmacy_purchase_orders'")
            index.delete()
            logger.info("Creating index 'hos_ecom_pharmacy_purchase_orders'")
            index.create()
        else:
            logger.info("Populating of index without deleting index.")
            if not index.exists():
                logger.info('No such `hos_ecom_pharmacy_purchase_orders` Index exists creating new one')
                index.create()
        filters = {
            "distributor_order_group__isnull": False,
            "tentative_delivery_date__range": ["2023-11-01", "2023-12-31"],
        }
        logger.info(f"Indexing {purchase_document.get_queryset(filters=filters).count()} objects.")
        qs = purchase_document.get_indexing_queryset(filters=filters)
        purchase_document.update(qs, parallel=True)
        logger.info('Data indexed successfully.')
