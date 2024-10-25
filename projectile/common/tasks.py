# -*- coding: ascii -*-
from __future__ import absolute_import, unicode_literals

import logging
import sys
import csv
import json
import requests
import importlib
import time
import os
import shutil

from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from core.models import SmsLog, Organization
from projectile.celery import app

from .enums import SmsLogType
from .slack_client import send_message_to_slack_channel
from .mattermost_client import send_message_to_mattermost_channel
from .ms_teams_client import send_message_to_teams_channel
from .helpers import send_log_alert_to_slack_or_mattermost

logger = logging.getLogger(__name__)


def prepare_headers():
    api_key = settings.INFOBIP_API_KEY
    headers = {}
    headers["Authorization"] = "App %s" % api_key
    headers["Accept"] = "application/json"
    headers["Content-Type"] = "application/json"
    return headers

# using requests module to post request to INFOBIP Api
def send_sms_single_client(sms_to, sms_text):
    url = 'https://api.infobip.com/sms/1/text/single/'
    data = {
        "to": sms_to,
        "text": sms_text
    }
    response = requests.post(url, headers=prepare_headers(), data=json.dumps(data))
    return response.content


def send_same_sms_to_multiple_client(receivers_list, sms_text):
    """[send same message to multiple client]
    Arguments:
        receivers_list {[list]} -- ['+8801xxxxxxxx, +8801xxxxxxxx', ...]
        sms_text {[str]} -- [text sms]
    """
    url = 'https://api.infobip.com/sms/1/text/advanced'
    destinations = [{'to': receiver} for receiver in receivers_list]
    data = {
        "messages":[
            {
                "destinations": destinations,
                "text": sms_text
            }
        ]
    }
    response = requests.post(url, headers=prepare_headers(), data=json.dumps(data))
    return response.json()


def send_bulk_sms_to_multiple_client(data):
    """[send different message to multiple client]
    Arguments:
        data {[list]} -- list of dictionary containing number and text
        sample: [
            {
                'to': '+8802xxxxxxxxxx',
                'text': 'bbbb'
            },
            {
                'to': '+8801xxxxxxxxxx',
                'text': 'aaaa'
            }
        ]
    """
    url = 'https://api.infobip.com/sms/1/text/advanced'
    data = {
        "messages": [{
            'destinations' : [{"to": item['to']}],
            "text": item['text']
            } for item in data]
    }
    response = requests.post(url, headers=prepare_headers(), data=json.dumps(data))
    return response.json()

@app.task
def send_sms(sms_to, sms_text, organization_id=None):
    time.sleep(1)
    """
    This method is used for sending single or bulksms

    Use 'sms_to' parameter as an array of phone numbers.
    """
    keep_sms_log_in = SmsLogType.DATABASE
    sms_log_file_name = 'sms-log.csv'
    # kept this configuration file here because to ensure
    # it's loaded by any mean (remember, celery tasks
    # can not connect to database)

    # send sms only if it is production mode
    if (not settings.DEBUG) and ('test' not in sys.argv):
        response = send_sms_single_client(sms_to, sms_text)

        logger.info("Phone No: {}".format(sms_to))
        logger.info("SMS Text: {}".format(sms_text))
        logger.info("Response: {}".format(response))

        # now save the responses to the SmsLog
        logger.info("Saving to SMS Log")

        if keep_sms_log_in == SmsLogType.CSV_FILE:
            with open(sms_log_file_name, 'a') as csv_file:
                sms_log_writer = csv.writer(csv_file)
                sms_log_writer.writerow([
                    timezone.now().strftime("%A  %H:%M:%S %d-%B-%Y"),
                    sms_to,
                    sms_text,
                    len(sms_text),
                    response,
                    organization_id,
                ])

        elif keep_sms_log_in == SmsLogType.DATABASE:
            sms_log = SmsLog(
                phone_number=sms_to,
                sms_body=sms_text,
                sms_count=len(sms_text),
                response_from_server=response,
                organization=Organization.objects.get(pk=organization_id)
            )
            sms_log.save()

        logger.info("Saved to SMS Log")

    else:
        logger.info("Phone No: {}".format(sms_to))
        logger.info("SMS Text: {}".format(sms_text))
        send_log_alert_to_slack_or_mattermost(sms_text)
        # now save the responses to the SmsLog
        logger.info("Saving to SMS Log")
        if keep_sms_log_in == SmsLogType.CSV_FILE:
            with open(sms_log_file_name, 'a') as csv_file:
                sms_log_writer = csv.writer(csv_file)
                sms_log_writer.writerow([
                    timezone.now().strftime("%A  %H:%M:%S %d-%B-%Y"),
                    sms_to,
                    sms_text,
                    len(sms_text),
                    '---',
                    organization_id,
                ])

        elif keep_sms_log_in == SmsLogType.DATABASE:
            sms_log = SmsLog(
                phone_number=sms_to,
                sms_body=sms_text,
                sms_count=len(sms_text),
                organization=Organization.objects.get(pk=organization_id)
            )
            sms_log.save()

        logger.info("Saved to SMS Log")

@app.task
def send_same_sms_to_multiple_receivers(receivers, sms_text):
    logger.info("Sending SMS to Support(Multiple)")
    logger.info("====================================>>")
    logger.info("Phone Numbers: {}".format(receivers))
    logger.info("SMS Text: {}".format(sms_text))

    if not settings.DEBUG and 'test' not in sys.argv:
        response = send_same_sms_to_multiple_client(receivers, sms_text)
        logger.info(response)
        try:
            sms_log = SmsLog(
                phone_number=','.join(receivers),
                sms_body=sms_text,
                sms_count=len(sms_text),
                response_from_server=response
            )
            sms_log.save()
            logger.info("Saved to SMS Log")
        except:
            logger.info("Failed to insert into SMS Log")
    else:
        try:
            sms_log = SmsLog(
                phone_number=','.join(receivers),
                sms_body=sms_text,
                sms_count=len(sms_text)
            )
            sms_log.save()
            logger.info("Saved to SMS Log")
        except:
            logger.info("Failed to insert into SMS Log")

# @app.task
def send_email(context, template, emails, subject):
    html_body = render_to_string(template, context)
    for email in emails:
        msg = EmailMultiAlternatives(subject=subject, bcc=[email],  headers={'BCc': email})
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        logger.info(u"Email sent... <Email: {}, Subject: {}>".format(emails, subject))

def get_model(model_string):
    """
    Return Model from module by model name
    Example #01:
        `get_model("pharmacy.models.Product")` will return `Product` model
    """
    last_dot_index = model_string.rfind('.')
    model_string_len = len(model_string)
    module_loc = model_string[0:last_dot_index]
    model_name = model_string[last_dot_index + 1: model_string_len]
    module = importlib.import_module(module_loc)
    return getattr(module, model_name)

def get_documents(model_string):
    from django_elasticsearch_dsl.registries import registry
    models = [
        get_model(model_string)
    ]
    documents = registry.get_documents(models)
    return documents

@app.task(bind=True, max_retries=10)
def custom_elastic_rebuild_on_bg(self, model_string, queryset_filter=None):
    from django_elasticsearch_dsl.registries import registry
    from django.db.models.query import QuerySet
    from requests import ConnectionError

    try:
        if queryset_filter is None:
            queryset_filter = {}
        for doc in get_documents(model_string):
            qs = doc().get_queryset(queryset_filter)
            doc().update(qs)
            logger.info(
                "Updated search index for {} with filter {}".format(model_string, queryset_filter))

    except ConnectionError as exc:
        logger.info('will retry in 5 sec')
        self.retry(exc=exc, countdown=5)

@app.task(bind=True, max_retries=10)
def custom_elastic_delete_on_bg(self, model_string, target_id):
    from elasticsearch.exceptions import NotFoundError, ConnectionError
    try:
        for doc in get_documents(model_string):
            target_instance = doc.get(target_id)
            doc.delete(target_instance)
            logger.info(
                "Deleting item by id({}) from `{}`".format(
                    target_id, model_string
                )
            )
    except ConnectionError as exc:
        logger.info('will retry in 5 sec')
        self.retry(exc=exc, countdown=5)
    except NotFoundError:
        pass
        # logger.error('Item `{}` not found in `{}`'.format(
        #     target_id,
        #     model_string
        # ))

@app.task(bind=True, max_retries=10)
def bulk_cache_write(self, cache_dictonary, timeout=settings.CACHES["default"]["TIMEOUT"]):
    cache.set_many(cache_dictonary, timeout)

@app.task(bind=True, max_retries=10)
def cache_write_lazy(self, cache_key, cache_data, timeout=settings.CACHES["default"]["TIMEOUT"]):
    cache.set(cache_key, cache_data, timeout)

@app.task(bind=True, max_retries=10)
def cache_expire(self, key):
    cache.delete(key)

@app.task(bind=True, max_retries=10)
def cache_pattern_expire(self, pattern):
    cache.delete_pattern(pattern, itersize=10000)

@app.task(bind=True, max_retries=10)
def cache_expire_list(self, key_list):
    # logger.info("deleting {} keys".format(len(key_list)))
    cache.delete_many(key_list)

@app.task
def send_message_to_slack_or_mattermost_channel_lazy(channel="", message=""):
    collaboration_service = os.environ.get("COLLABORATION_SERVICE", "SLACK")
    if collaboration_service == "MATTERMOST":
        send_message_to_mattermost_channel(channel, message)
    elif collaboration_service == "TEAMS":
        send_message_to_teams_channel(channel, message)
    else:
        send_message_to_slack_channel(channel, message)

@app.task(autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=5, max_retries=10)
def delete_directory_lazy(directory_path):
    try:
        shutil.rmtree(directory_path)
    except Exception as e:
        logger.debug(e)
