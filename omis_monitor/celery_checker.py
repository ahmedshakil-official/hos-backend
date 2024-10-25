"""
Celery checker function
"""


def check_celery(json_obj, logger):
    try:
        if json_obj['ERROR']:
            logger.critical('Celery is down')
            return False
        else:
            logger.debug('Celery is running')
            return True
    except Exception:
        logger.debug('Celery is running')
        return True
