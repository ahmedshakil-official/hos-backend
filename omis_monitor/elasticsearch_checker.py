"""
ElasticSearch checker function
"""


def check_elastic_search(json_obj, logger):
    try:
        logger.debug('ElasticSearch Cluster: {} is running'.format(json_obj['cluster_name']))
        return True
    except Exception:
        logger.critical('ElasticSearch is down')
        return False
