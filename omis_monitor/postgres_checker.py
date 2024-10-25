"""
Postgres checker function
"""


def check_postgres(json_obj, logger):
    try:
        logger.debug('Database: {} is running'.format(json_obj[0]['name']))
        return True
    except Exception:
        logger.critical('Postgres is down')
        return False
