"""
This is the configuration for the omis checker daemon
This app is intent to check services periodically
"""

# log
import logging
import logging.handlers

import os

HEARTBEAT = {
    'URL': "{0}/heartbeat/1337/".format(os.environ.get('APP_URL', 'http://localhost:8000')),
    'USERNAME': 'omis',
    'PASSWORD': os.environ.get('HEARTBEAT_PASSWORD', 'supersecret'),
}

EMAIL = {
    'ENABLED': True,
    'TO': ['ashraful.alam@interconnectionbd.com', ],
    'FROM': 'postmaster@sandbox34045.mailgun.org',
    'HOST': os.environ.get('SMTP_HOST', ''),
    'PORT': os.environ.get('SMTP_PORT', ''),
    'USERNAME': os.environ.get('SMTP_USERNAME', ''),
    'PASSWORD': os.environ.get('SMTP_PASSWORD', ''),
}

SMS = {
    'ENABLED': True,
    'TO': [os.environ.get('OMIS_MONITOR_SMS_TO', '')],
    'INFOBIP_API_KEY': os.environ.get('INFOBIP_API_KEY', ''),
}


def get_logger(name):
    log_filename = 'omis_monitor.log'

    logging.basicConfig(
        filename=log_filename,
        level=logging.NOTSET,
        format='%(asctime)s [%(levelname)s]: %(message)s'
    )

    # Set up a specific logger with our desired output level
    logger = logging.getLogger('OMISLogger')
    return logger
