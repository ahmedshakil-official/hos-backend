import os

from django.core.cache import cache
from django.db import transaction

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, parsers
from rest_framework.exceptions import ValidationError

from common.tasks import send_message_to_slack_or_mattermost_channel_lazy
from common.utils import generate_map_url_and_address_from_geo_data
from common.enums import Status
from common.cache_keys import DUPLICATE_USER_CREATION_CACHE_KEY_PREFIX
from ..models import Organization
from ..serializers import (
    PasswordResetRequestSerializer,
    EcommerceUserRegistrationSerializer,
    AuthFailureLogSerializer,
)


class PasswordResetRequest(APIView):
    permission_classes = ()

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            pharmacy_name = serializer.data.get("pharmacy_name", "")
            mobile_no = serializer.data.get("mobile_no", "")
            map_address = generate_map_url_and_address_from_geo_data(request.headers)
            healthos_sms_text = "New password reset request.\nPharmacy Name: {},\nMobile No: {}, \nAddress: {}(Approx.), \nGoogle Map: {}".format(
                pharmacy_name,
                mobile_no,
                map_address.get("address", "Not Found"),
                map_address.get("map_url", "Not Found")
            )
            # Send message to slack channel
            send_message_to_slack_or_mattermost_channel_lazy.delay(
                os.environ.get("HOS_PASSWORD_RESET_REQUEST_CHANNEL_ID", ""),
                healthos_sms_text
            )
            return Response({"message": "Success"}, status=status.HTTP_201_CREATED)
        return Response({"message": "Failed"}, status=status.HTTP_400_BAD_REQUEST)


class EcomUserRegistration(generics.CreateAPIView):

    serializer_class = EcommerceUserRegistrationSerializer
    permission_classes = ()
    ATOMIC_REQUESTS = True
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser)

    def perform_create(self, serializer):
        phone = self.request.data.get('phone')
        cache_key = f"{DUPLICATE_USER_CREATION_CACHE_KEY_PREFIX}{phone}"

        # Check for duplicate request
        if cache.get(cache_key):
            error = {
                "error": "Please wait, we are processing your request!"
            }
            raise ValidationError(error)

        # Set the cache key to prevent further duplicate requests
        cache.set(key=cache_key, value=True, timeout=60)

        # Calling the serializer's save method to handle the actual creation
        serializer.save()
        cache.delete(cache_key)

class AuthLog(generics.CreateAPIView):

    serializer_class = AuthFailureLogSerializer
    permission_classes = ()


class OrganizationSubAreaList(APIView):
    permission_classes = ()

    def get(self, request):
        try:
            keyword = self.request.query_params.get('keyword', None)
            organization_sub_areas = Organization.objects.filter(
                status=Status.ACTIVE,
                delivery_sub_area__isnull=False
            ).values_list('delivery_sub_area', flat=True)
            if keyword:
                organization_sub_areas = organization_sub_areas.filter(
                    delivery_sub_area__icontains=keyword
                )
            return Response(set(sorted(organization_sub_areas)), status=status.HTTP_200_OK)
        except Exception as exception:
            return Response({"message": "Failed"}, status=status.HTTP_400_BAD_REQUEST)
