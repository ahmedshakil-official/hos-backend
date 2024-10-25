import json
import urllib3
from django.conf import settings


def check(request):
    """
    :param request: HttpRequest object
    :return: dict
    """

    # Checker logic goes here
    http = urllib3.PoolManager()
    try:
        req = http.request('GET', 'http://{}:9200/'.format(settings.ELASTICSEARCH_DSL['default']['hosts']))
        return json.loads(req.data.decode('utf-8'))

    except urllib3.exceptions.NewConnectionError:
        return 'ElasticSearch is down.'

    except urllib3.exceptions.MaxRetryError:
        return 'ElasticSearch is down.'
