import os
import redis
from django.conf import settings


def check(request):
    """
    :param request: HttpRequest object
    :return: dict
    """

    # Checker logic goes here
    try:
        # set the redis credentials
        redis_client = redis.Redis(
            host=os.environ.get('REDIS_SERVER_IP'),
        )

        # ping the redis server
        if redis_client.ping():
            return 'Redis is running.'
        else:
            return 'Redis is down.'

    except redis.ConnectionError:
        return 'Redis is down.'
