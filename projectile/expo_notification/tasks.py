# -*- coding: ascii -*-
from __future__ import absolute_import, unicode_literals
import os
import json
from onesignal_sdk.client import Client
import logging
import time

from projectile.celery import app

from exponent_server_sdk import PushClient
from exponent_server_sdk import PushMessage

from common.enums import Status

from .models import PushToken, PushNotification

logger = logging.getLogger(__name__)


@app.task
def send_push_notification_to_mobile_app(user_id, notification_id=None, title="", body="", data="", image="", entry_by_id=None):
    try:
        push_tokens = PushToken.objects.filter(
            status=Status.ACTIVE,
            active=True,
            user_id=user_id
        ).only('id', 'user', 'token', 'player_id')
        data_list = []
        invalid_push_token_ids = []
        data = None if data == "" else data
        for push_token in push_tokens:
            if push_token.player_id is not None:
                client = Client(
                    app_id=os.environ.get('ONESIGNAL_APP_ID', None),
                    rest_api_key=os.environ.get('ONESIGNAL_REST_API_KEY', None),
                    user_auth_key=push_token.player_id
                )
                notification_body = {
                    'contents': {'en': body},
                    'headings': {'en': title},
                    'data': data,
                    'big_picture': image,
                    'include_player_ids': [push_token.player_id],
                }
                response = client.send_notification(notification_body)
                data_list.append(PushNotification(
                    token_id=push_token.id,
                    user_id=user_id,
                    notification_id=notification_id,
                    body=body,
                    data=data or {},
                    title=title,
                    response=response.body,
                    entry_by_id=entry_by_id
                ))
                if response.body is not None and 'errors' in response.body:
                    errors = response.body.get('errors')
                    if errors == ['All included players are not subscribed'] or 'invalid_player_ids' in errors:
                        invalid_push_token_ids.append(push_token.id)
            else:
                response = PushClient().publish(
                    PushMessage(
                        to=push_token.token,
                        data=data,
                        title=title,
                        body=body,
                        sound="default"
                    )
                )
                data_list.append(PushNotification(
                    token_id=push_token.id,
                    user_id=user_id,
                    notification_id=notification_id,
                    body=body,
                    data=data or {},
                    title=title,
                    response=response,
                    entry_by_id=entry_by_id

                ))
                if response.details is not None:
                    if response.details.get('error', None) == "DeviceNotRegistered":
                        invalid_push_token_ids.append(push_token.id)

        logger.info("Successfully sent notification to {}".format(user_id))
        PushNotification.objects.bulk_create(data_list)
        # Mark the push token as inactive
        if invalid_push_token_ids:
            PushToken.objects.filter(pk__in=invalid_push_token_ids).update(active=False)
    except Exception as exception:
        logger.warning(
            "Unable to send notification, Exception: {}".format(
                str(exception)
            )
        )


@app.task
def send_push_notification_to_mobile_app_by_org(org_ids=None, notification_id=None, title="", body="", data="", url="", image="", large_icon="", entry_by_id=None, min_id=None, max_id=None):
    try:
        if org_ids:
            push_tokens = PushToken.objects.filter(
                status=Status.ACTIVE,
                active=True,
                user__organization__id__in=org_ids
            ).only('id', 'user', 'token', 'player_id')
        elif (min_id and max_id):
            push_tokens = PushToken.objects.filter(
                status=Status.ACTIVE,
                active=True,
                user__organization__id__range=[min_id, max_id]
            ).only('id', 'user', 'token', 'player_id')
        else:
            push_tokens = PushToken.objects.filter(
                status=Status.ACTIVE,
                active=True,
            ).only('id', 'user', 'token', 'player_id')
        data_list = []
        invalid_push_token_ids = []
        data = None if data == "" else data
        for push_token in push_tokens:
            if push_token.player_id is not None:
                client = Client(
                    app_id=os.environ.get('ONESIGNAL_APP_ID', None),
                    rest_api_key=os.environ.get('ONESIGNAL_REST_API_KEY', None),
                    user_auth_key=push_token.player_id
                )
                notification_body = {
                    'contents': {'en': body},
                    'headings': {'en': title},
                    'data': data,
                    'url': url,
                    'big_picture': image,
                    'large_icon': large_icon,
                    'include_player_ids': [push_token.player_id],
                }
                response = client.send_notification(notification_body)
                data_list.append(PushNotification(
                    token_id=push_token.id,
                    user_id=push_token.user_id,
                    notification_id=notification_id,
                    body=body,
                    data=data or {},
                    title=title,
                    url=url,
                    response=response.body,
                    entry_by_id=entry_by_id
                ))
                if response.body is not None and 'errors' in response.body:
                    errors = response.body.get('errors')
                    if errors == ['All included players are not subscribed'] or 'invalid_player_ids' in errors:
                        invalid_push_token_ids.append(push_token.id)
            else:
                response = PushClient().publish(
                    PushMessage(
                        to=push_token.token,
                        data=data,
                        title=title,
                        body=body,
                        sound="default"
                    )
                )
                data_list.append(PushNotification(
                    token_id=push_token.id,
                    user_id=push_token.user_id,
                    notification_id=notification_id,
                    body=body,
                    data=data or {},
                    title=title,
                    response=response,
                    entry_by_id=entry_by_id

                ))
                if response.details is not None:
                    if response.details.get('error', None) == "DeviceNotRegistered":
                        invalid_push_token_ids.append(push_token.id)
        logger.info("Successfully sent notification.")
        PushNotification.objects.bulk_create(data_list)
        # Mark the push token as inactive
        if invalid_push_token_ids:
            PushToken.objects.filter(pk__in=invalid_push_token_ids).update(active=False)
    except Exception as exception:
        logger.warning(
            "Unable to send notification, Exception: {}".format(
                str(exception)
            )
        )
