import os
import logging
import pandas as pd

from tqdm import tqdm
from django.core.management.base import BaseCommand
from common.enums import Status
from core.models import PersonOrganization
from core.enums import PersonGroupType
from projectile.settings import REPO_DIR

logger = logging.getLogger(__name__)

def fix_employee_code(data_frame):
    total_data = len(data_frame.index)
    success_count = 0
    failed_count = 0
    failed_data = []
    distributor_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
    for _, item in tqdm(data_frame.iterrows()):
        code = item.get('ID', '')
        phone = item.get('Contact', '')
        name = item.get('Name', '')
        if code and phone and name:
            try:
                po_instance = PersonOrganization.objects.only(
                    'code',
                    'person',
                    'person__code',
                ).exclude(
                    status=Status.INACTIVE
                ).get(
                    phone=phone,
                    person_group=PersonGroupType.EMPLOYEE,
                    organization__id=distributor_id
                )
                po_instance.code = code
                po_instance.person.code = code
                po_instance.save(update_fields=['code'])
                po_instance.person.save(update_fields=['code'])
                success_count += 1

            except PersonOrganization.DoesNotExist:
                failed_count += 1
                failed_data.append({
                    'code': code,
                    'phone': phone,
                    'name': name,
                    'reason': "No Person Organization Instance Found"
                })

            except PersonOrganization.MultipleObjectsReturned:
                failed_count += 1
                failed_data.append({
                    'code': code,
                    'phone': phone,
                    'name': name,
                    'reason': "Multiple Person Organization Instance Found"
                })

            except:
                failed_count += 1
                pass
    logger.info(f"Successfully updated {success_count}, failed {failed_count} out of {total_data}")
    if failed_data:
        logger.error(failed_data)






class Command(BaseCommand):
    def handle(self, **options):
        logger.info("Fixing employee code from csv file......")
        file_path = os.path.join(REPO_DIR, 'tmp/employee_list.csv')
        data_frame = pd.read_csv(file_path, dtype=object, index_col=0)
        new_df = data_frame.dropna(how="all", inplace=True)
        fix_employee_code(data_frame)

