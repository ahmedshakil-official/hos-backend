import json
import requests

import config
from elasticsearch_checker import check_elastic_search
from redis_checker import check_redis
from postgres_checker import check_postgres
from celery_checker import check_celery
from send_email import send_email
from send_sms import send_sms


def main():
    instance_status = {
        'elasticsearch': False,
        'celery': False,
        'redis': False,
        'postgres': False,
        'django': False,
        'heartbeat': False,
    }

    try:
        logger = config.get_logger('main')
        logger.debug('Connecting to Django HeartBeat')
        req = requests.get(
            config.HEARTBEAT['URL'],
            auth=(
                config.HEARTBEAT['USERNAME'],
                config.HEARTBEAT['PASSWORD']
            )
        )

        if req.status_code == 200:
            logger.info('Django HeartBeat connected')
            # json parse
            res = json.loads(req.content)
            # change the status of django & heartbeat
            instance_status['django'] = True
            instance_status['heartbeat'] = True

            # check elasticsearch
            instance_status['elasticsearch'] = check_elastic_search(res['elasticsearch_checker'], logger)

            # check redis
            instance_status['redis'] = check_redis(res['redis_checker'], logger)

            # check postgres
            instance_status['postgres'] = check_postgres(res['databases'], logger)

            # check postgres
            instance_status['celery'] = check_celery(res['celery_checker'], logger)

        else:
            logger.error('Django HeartBeat is down')
            instance_status['heartbeat'] = False

    except Exception:
        logger.critical('Django Server is down')
        instance_status['django'] = False

    # search the cashed services
    crashed_instances = {key: val for key, val in instance_status.items() if val == False}

    if len(crashed_instances):
        # Something is not right, send notifications
        if config.EMAIL['ENABLED']:
            # Email is enabled, send email
            text = ''
            html = ''
            for (service_name, val) in crashed_instances.items():
                text += '{}, '.format(service_name)
                html += '<li>{}</li>'.format(service_name)

            text = 'These service(s) are down: {}'.format(text[:-2])
            html = 'These service(s) are down: <ul>{}</ul>'.format(html)
            send_email([text, html], logger)


        if config.SMS['ENABLED']:
            # SMS is enabled, send SMS
            text = ''
            for (service_name, val) in crashed_instances.items():
                text += '{}, '.format(service_name)
            text = 'These service(s) are down: {}'.format(text[:-2])
            send_sms(text, logger)


# run the main function if needed
if __name__ == '__main__':
    main()
