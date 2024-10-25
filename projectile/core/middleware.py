import logging

from collections import Counter
from operator import itemgetter

from pprint import pformat
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

from common import models

logger = logging.getLogger(__name__)

# pylint: disable=old-style-class, no-init
class LogSQLMiddleware(MiddlewareMixin):

    calls = Counter()
    queries = Counter()

    def process_response(self, request, response):
        """Log the SQL queries that the request ran"""
        logger.debug('SQL Queries for request {}:\n{}'.format(
            request.path, pformat(connection.queries)))
        logger.debug('Total SQL Queries for request {}: {}'.format(
            request.path, len(connection.queries)))
        self.calls[request.path] += 1
        self.queries[request.path] += len(connection.queries)
        averages = [(ep, self.queries[ep] / float(self.calls[ep])
                     if self.calls[ep] else 0.0) for ep in self.queries]
        averages.sort(key=itemgetter(1))
        logger.debug('Endpoint averages:\n{}'.format(
            '\n'.join('{}: {}'.format(ep, avg) for ep, avg in averages)))
        return response


class RequestInformationMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE', 'GET']:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[-1].strip()
            elif request.META.get('HTTP_X_REAL_IP'):
                ip_address = request.META.get('HTTP_X_REAL_IP')
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            models.USER_IP_ADDRESS = ip_address
            request.user_ip = ip_address
