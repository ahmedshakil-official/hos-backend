import logging
from tqdm import tqdm
import pandas as pd

from django.core.management.base import BaseCommand

from core.models import Organization

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, **options):
        logger.info("UPDATING SUB AREA FOR UTTARA DELIVERY HUB.....")
        org_sub_area_file = "tmp/uttara_sub_area_update.csv"
        data_df = pd.read_csv(org_sub_area_file)
        data_df = data_df.fillna("")
        org_id_list = data_df['ID'].tolist()
        update_count = 0
        failed_count = 0
        for index, row in tqdm(data_df.iterrows()):
            org_id = row.get("ID", "")
            new_sub_area = row.get("NEW_SUB_AREA", "")
            try:
                organization_instance = Organization.objects.only("delivery_sub_area").get(pk=org_id)
                organization_instance.delivery_sub_area = new_sub_area
                organization_instance.save(update_fields=["delivery_sub_area"])
                update_count += 1
            except:
                failed_count += 1
        logger.info(f"{update_count} ORG SUB AREAS UPDATED, {failed_count} FAILED.")
