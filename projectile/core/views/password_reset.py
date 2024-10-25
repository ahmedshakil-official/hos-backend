import os
import random
import string

from datetime import datetime, timedelta

from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from rest_framework import status
from rest_framework.views import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView

from common.helpers import generate_phone_no_for_sending_sms
from common.utils import generate_map_url_and_address_from_geo_data
from core.choices import OtpType, ResetStatus, ResetType
from core.permissions import (
    AnyLoggedInUser,
    CheckAnyPermission,
    IsAuthenticatedOrCreate,
    IsSuperUser,
    StaffIsAdmin,
)

from core.models import PasswordReset, Person, OTP, Organization, PersonOrganization

from core.custom_serializer.password_reset import PasswordResetModelSerializer, UserPasswordResetSerializer
from core.utils import generate_unique_otp
from common.tasks import send_sms, send_message_to_slack_or_mattermost_channel_lazy


class PasswordResetList(ListCreateAPIView):
    available_permission_classes = ()
    serializer_class = PasswordResetModelSerializer.List

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PasswordResetModelSerializer.List
        return PasswordResetModelSerializer.Post

    def get_queryset(self, related_fields=None, only_fields=None):
        return PasswordReset().get_all_actives()

    def get_permissions(self):
        if self.request.method == "GET":
            self.available_permission_classes = (
                StaffIsAdmin,
            )
        else:
            self.available_permission_classes = (
                IsAuthenticatedOrCreate,
            )
        return (CheckAnyPermission(),)


class UserPasswordReset(APIView):
    permission_classes = ()

    def post(self, request):
        # Deserialize the request data using UserPasswordResetSerializer
        serializer = UserPasswordResetSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            phone = serializer.validated_data.get("phone", None)
            pharmacy_name = serializer.validated_data.get("pharmacy_name", None)
            new_password = serializer.validated_data.get("new_password", None)
            confirm_password = serializer.validated_data.get("confirm_password", None)
            otp = serializer.validated_data.get("otp", None)

            try:
                # Check if a user with the provided phone number exists
                user = Person().get_all_actives().get(phone=phone)
            except Person.DoesNotExist:
                return Response(
                    {"detail": "Person with the provided phone number does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if phone and pharmacy_name:
                #  Create a PasswordReset entry
                PasswordReset.objects.create(
                    user_id=user.id,
                    phone=phone,
                    reset_status=ResetStatus.PENDING,
                    type=ResetType.MANUAL,
                    name=pharmacy_name,
                    organization=user.organization,
                )

                # get user map address from request headers
                map_address = generate_map_url_and_address_from_geo_data(request.headers)

                # Compose messages for mattermost channel
                healthos_sms_text = "New password reset request.\nPharmacy Name: {},\nMobile No: {}, \nAddress: {}(Approx.), \nGoogle Map: {}".format(
                    pharmacy_name,
                    phone,
                    map_address.get("address", "Not Found"),
                    map_address.get("map_url", "Not Found")
                )
                # Send message to Slack channel
                send_message_to_slack_or_mattermost_channel_lazy.delay(
                    os.environ.get("HOS_PASSWORD_RESET_REQUEST_CHANNEL_ID", ""),
                    healthos_sms_text
                )

                return Response({"message": "Success"}, status=status.HTTP_201_CREATED)

            elif phone and not pharmacy_name:

                if not otp:
                    # Check if there is an existing OTP created in the last 5 minutes
                    five_minutes_ago = datetime.now() - timedelta(minutes=5)
                    existing_otp = OTP.objects.filter(
                        user_id=user.id,
                        type=OtpType.PASSWORD_RESET,
                        is_used=False,
                        created_at__gte=five_minutes_ago,
                    ).exists()

                    if existing_otp:
                        # User already has a valid OTP created in the last 5 minutes
                        return Response({
                            'detail': "You already have an OTP. Please wait for the message."
                        }, status=status.HTTP_400_BAD_REQUEST)

                    else:
                        # Generate a new OTP and send it to the user's phone
                        otp = generate_unique_otp()
                        OTP.objects.create(
                            user_id=user.id,
                            otp=otp,
                            type=OtpType.PASSWORD_RESET
                        )

                        # Sending sms
                        message = f"Your HealthOS OTP is {otp}, It's valid for 5 minutes."
                        phone_number = generate_phone_no_for_sending_sms(user.phone)
                        send_sms.delay(phone_number, message, user.organization.id)

                        # Return a response indicating that OTP will be sent to the user's phone
                        return Response({
                            "detail": "OTP has sent to your phone number.",
                            "code": "OTP"
                        }, status=status.HTTP_200_OK)
                else:
                    if new_password and confirm_password:

                        # Validate the new password using AUTH_PASSWORD_VALIDATORS
                        try:
                            password_validation.validate_password(new_password, user)
                        except ValidationError as e:
                            # Handle the validation error
                            return Response({"password": e.messages}, status=status.HTTP_400_BAD_REQUEST)

                        # If both password not matched return error
                        if new_password != confirm_password:
                            return Response({
                                "detail": "new password and confirm password not matched"
                            }, status=status.HTTP_400_BAD_REQUEST)

                        try:
                            # Verify the OTP provided by the user
                            otp_record = OTP.objects.get(
                                user_id=user.id,
                                otp=otp,
                                is_used=False,
                                type=OtpType.PASSWORD_RESET
                            )

                        except OTP.DoesNotExist:
                            return Response({
                                "detail": "Invalid OTP."
                            }, status=status.HTTP_400_BAD_REQUEST)

                        if timezone.now() < (otp_record.created_at + timedelta(minutes=5)):
                            # Update the user's password
                            user.password = make_password(new_password)
                            user.save(update_fields=['password'])

                            # Mark the OTP as used
                            otp_record.is_used = True
                            otp_record.save(update_fields=['is_used'])

                            PasswordReset.objects.create(
                                user_id=user.id,
                                phone=phone,
                                organization_id=user.organization_id,
                                reset_status=ResetStatus.SUCCESS,
                                otp_id=otp_record.id,
                                type=ResetType.SELF
                            )

                            return Response({
                                "detail": "Password reset successfully done"
                            }, status=status.HTTP_200_OK)
                        else:
                            return Response({
                                "detail": "OTP has expired."
                            }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({
                            "detail": "Please provide new password and confirm password"
                        }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
