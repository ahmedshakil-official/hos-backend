import os
import json
import requests
import logging

from django.core.management.base import BaseCommand

from reporter_proxy.helpers import set_token


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate JWT for reporter proxy"

    def handle(self, *args, **options):
        base_url = os.environ.get("REPORTER_BASE_URL", "")
        api_url = f"{base_url}/api/v1/token"
        phone = input("Enter Phone or Email: ")
        password = input("Enter Password: ")
        payload = {"phone": phone, "password": password}
        logger.info("Generating access and refresh token....")
        response = requests.post(api_url, json=payload)
        response_data = response.json()
        access_token = response_data.get("access", "")
        refresh_token = response_data.get("refresh", "")
        # Set the token to cache
        set_token(access_token, refresh_token)
        logger.info("Done!!!")
