"""Serializer for Password Reset Model."""

from django.db.models import Q
from rest_framework import serializers

from core.models import PasswordReset, Person

from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer


class PasswordResetMeta(ListSerializer.Meta):
    model = PasswordReset
    fields = ListSerializer.Meta.fields + (
        "name",
        "phone",
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
    )


class PasswordResetModelSerializer:
    class List(ListSerializer):
        class Meta(PasswordResetMeta):
            fields = PasswordResetMeta.fields + (
                "user",
                "organization",
                "otp",
                "reset_status",
                "type",
            )
            read_only_fields = ListSerializer.Meta.read_only_fields + ()

    class Post(ListSerializer):
        class Meta(PasswordResetMeta):
            fields = PasswordResetMeta.fields + (
                "type",
            )
            read_only_fields = ListSerializer.Meta.read_only_fields + ()

        def create(self, validated_data):
            phone_number = validated_data.get("phone")

            # Try searching with different variations of the phone number
            possible_numbers = [phone_number]
            if phone_number.startswith("0"):
                possible_numbers.append(phone_number[1:])
            else:
                possible_numbers.append("0" + phone_number)

            user = Person.objects.filter(
                Q(phone=possible_numbers[0]) | Q(phone=possible_numbers[1])
            ).first()

            pharmacy_name = validated_data.get("name")
            reset_status = validated_data.get("reset_status", None)
            reset_type = validated_data.get("type", None)

            reset_request_data = {
                "name": pharmacy_name,
                "user_id": user.id if user else None,
                "phone": phone_number,
                "organization_id": user.organization_id if user and user.organization_id else None,
            }
            if reset_type:
                reset_request_data["type"] = reset_type

            instance = self.Meta.model(**reset_request_data)
            instance.save()
            return instance


class UserPasswordResetSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset OTP or CC.
    """
    phone = serializers.CharField(required=True, allow_blank=True, allow_null=True)
    pharmacy_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    new_password = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    confirm_password = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    otp = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        write_only=True
    )
