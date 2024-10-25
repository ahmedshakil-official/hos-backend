import logging
from datetime import date
import pandas as pd
from tqdm import tqdm
from django.core.management.base import BaseCommand
from common.enums import Status
from common.helpers import get_date_from_period
from pharmacy.models import StockIOLog
from procurement.models import ProcureItem

logger = logging.getLogger(__name__)

def update_rate_for_requisition_io(requisition_id, entries):
    requisition_ios = StockIOLog.objects.filter(
        purchase_id=requisition_id,
    ).exclude(status=Status.INACTIVE).only("stock_id", "rate").order_by()
    ios_to_be_updated = []
    for requisition_io in requisition_ios:
        row = entries.loc[entries["stock_id"] == requisition_io.stock_id]
        try:
            rate = row["rate"].iloc[0]
        except:
            rate = 0
        requisition_io.rate = float(rate)
        ios_to_be_updated.append(requisition_io)
    StockIOLog.objects.bulk_update(
        ios_to_be_updated,
        ["rate"],
        batch_size=1000
    )

def populate_rate():
    procure_items = ProcureItem().get_all_actives().filter(
        date__range=[
            get_date_from_period("1m"),
            date.today()
        ]
    ).exclude(
        procure__requisition__isnull=True
    ).values(
        "procure_id",
        "stock_id",
        "procure__requisition_id",
        "rate"
    )

    procure_items_data_df = pd.DataFrame(procure_items)
    if not procure_items_data_df.empty:
        procure_items_data_df = procure_items_data_df.groupby("procure__requisition_id")

        for key, entries in tqdm(procure_items_data_df):
            requisition_id = key
            if not entries.empty:
                update_rate_for_requisition_io(requisition_id, entries)

class Command(BaseCommand):
    def handle(self, **options):
        logger.info("POPULATING RATE OF REQUISITION BASED ON LAST 1 MONTH's PROCUREMENTS....")
        populate_rate()
        logger.info("Done!!!")
