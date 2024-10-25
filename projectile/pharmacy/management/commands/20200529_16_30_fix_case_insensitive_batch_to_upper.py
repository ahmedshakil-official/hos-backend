import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db.models import Q, F, Min, Max
from django.db.models.functions import Upper, Lower
from pharmacy.models import StockIOLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, **options):
        update_count = 0
        logger.info("UPDATING STOCK IO LOG BATCH TO CASE SENSITIVE UPPER CASE")
        stock_io_logs = StockIOLog.objects.filter(~Q(batch__exact=Upper('batch')))
        update_count = stock_io_logs.count()
        chunk_size = 5000
        if update_count > chunk_size:
            dict_ = stock_io_logs.aggregate(Max('id'), Min('id'))
            max_id = dict_['id__max']
            min_id = dict_['id__min']
            while min_id <= max_id:
                max_range = min_id + chunk_size - 1
                max_range = max_id if max_range > max_id else max_range
                logger.info("UPDATING CHUNK BETWEEN {} to {}".format(min_id, max_range))
                StockIOLog.objects.filter(
                    id__range=[min_id, max_range]
                ).update(batch=Upper('batch'))
                min_id += chunk_size
        else:
            stock_io_logs.update(batch=Upper('batch'))

        if update_count > 0:
            logger.info("{} STOCK IO LOG UPDATED.".format(update_count))
        else:
            logger.info("NOTHING UPDATED.")
