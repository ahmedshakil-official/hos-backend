"""
Redis checker function
"""


def check_redis(message, logger):
    if message.find('running') > -1:
        logger.debug('Redis is running')
        return True
    else:
        logger.critical('Redis is down')
        return False
