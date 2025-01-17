import logging
import time

from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

# pylint: disable=invalid-name
class throttle(object):
    """
    Source: https://gist.github.com/ChrisTM/5834503

    Decorator that prevents a function from being called more than once every
    time period.

    To create a function that cannot be called more than once a minute:

        @throttle(minutes=1)
        def my_fun():
            pass
    """

    def __init__(self, seconds=0, minutes=0, hours=0):
        self.throttle_period = timedelta(
            seconds=seconds, minutes=minutes, hours=hours
        )
        self.time_of_last_call = datetime.min

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            now = datetime.now()
            time_since_last_call = now - self.time_of_last_call

            if time_since_last_call > self.throttle_period:
                self.time_of_last_call = now
                return fn(*args, **kwargs)

        return wrapper


def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        # pylint: disable=logging-not-lazy
        logger.info('%r (%r, %r) %2.2f sec' %
                    (method.__name__, args, kw, te - ts))
        return result

    return timed
