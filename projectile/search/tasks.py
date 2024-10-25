import logging

from elasticsearch.exceptions import ConnectionTimeout
from projectile.celery import app
from search.utils import update_stock_es_doc

logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=10)
def update_stock_document_lazy(self, filters={}):
    try:
        update_stock_es_doc(filters)
    except Exception as exc:
        logger.info('will retry in 5 sec')
        self.retry(exc=exc, countdown=5)
