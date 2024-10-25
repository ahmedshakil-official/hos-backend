"""Serializers for Procure payment"""

from decimal import Decimal

from django.db import transaction

from rest_framework import serializers
from rest_framework.validators import ValidationError

from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer

from procurement.enums import ProcurePaymentMethod
from procurement.models import Procure, ProcurePayment
from procurement.serializers.procure import ProcureModelSerializer
from procurement.utils import calculate_procure_payment_data

DECIMAL_ZERO = Decimal('0.00')


class ProcurePaymentMeta(ListSerializer.Meta):
    model = ProcurePayment
    fields = ListSerializer.Meta.fields + (
        "date",
        "procure"
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + ()


class ProcurePaymentModelSerializer:
    class List(ListSerializer):
        procure = ProcureModelSerializer.Lite(read_only=True)

        class Meta(ProcurePaymentMeta):
            fields = ProcurePaymentMeta.fields + (
                "amount",
                "method",
                "method_reference"
            )
            read_only_fields = ProcurePaymentMeta.read_only_fields + ()

    class Post(ListSerializer):
        procure = serializers.SlugRelatedField(
            queryset=Procure().get_all_non_inactives(),
            slug_field="alias",
            error_messages={
                "detail": "Procure doesn't exists"
            },
            write_only=True
        )

        class Meta(ProcurePaymentMeta):
            fields = ProcurePaymentMeta.fields + (
                "amount",
                "method",
                "method_reference"
            )
            read_only_fields = ProcurePaymentMeta.read_only_fields + ()

        @transaction.atomic
        def create(self, validated_data):
            """
            Create a new payment record.

            This method creates a new payment record based on the provided validated data. It performs validation checks to ensure
            that the payment amount, method, and reference (if required) are provided correctly, and the amount does not exceed the
            open credit balance or credit amount of the associated procure.

            Args:
                validated_data (dict): The validated data to create the payment record.

            Returns:
                Payment: The newly created payment instance.
            """

            procure = validated_data.get("procure", None)
            amount = validated_data.get("amount", DECIMAL_ZERO)
            method = validated_data.get("method", None)
            method_reference = validated_data.get("method_reference", "")

            user = self.context.get("request").user
            validated_data["entry_by"] = user
            validated_data["organization"] = user.organization

            # Validate payment amount
            if amount == DECIMAL_ZERO:
                raise ValidationError(
                    {
                        "detail": "Please provide payment amount."
                    }
                )

            # Validate payment method
            if amount > DECIMAL_ZERO and method is None:
                raise ValidationError(
                    {
                        "detail": "Please provide payment method."
                    }
                )

            # Validate reference for specific payment methods
            if (
                    method
                    and method in (
                    ProcurePaymentMethod.CHEQUE,
                    ProcurePaymentMethod.BKASH,
                    ProcurePaymentMethod.NAGAD)
                    and method_reference == ""
            ):
                raise ValidationError(
                    {"detail": "For CHEQUE, BKASH, and NAGAD, a reference number is mandatory."}
                )

            # Ensure the payment amount does not exceed open credit balance
            if amount > procure.open_credit_balance:
                raise ValidationError(
                    {"detail": "Amount can't be greater than the open credit balance"}
                )

            # Ensure the total paid amount does not exceed the credit amount
            total_paid_amount = procure.paid_amount + amount
            if total_paid_amount > procure.credit_amount:
                raise ValidationError(
                    {"detail": "Amount can't be greater than the credit amount"}
                )

            # Create the payment record
            instance = super().create(validated_data=validated_data)

            # Update Procure paid amount and open credit balance
            calculate_procure_payment_data(procure)

            return instance

        @transaction.atomic
        def update(self, instance, validated_data):
            """
                Update an existing payment record.

                This method updates an existing payment record based on the provided validated data. It performs validation checks to ensure
                that the payment amount, method, and reference (if required) are provided correctly, and the amount does not exceed the
                open credit balance or credit amount of the associated procurement. After updating the payment record, it also updates
                the paid amount and open credit balance of the associated procurement.

                Args:
                    instance (ProcurePayment): The existing payment instance to be updated.
                    validated_data (dict): The validated data used for updating the payment record.

                Returns:
                    Payment: The updated payment instance.
            """
            procure = validated_data.get("procure", None)
            amount = validated_data.get("amount", DECIMAL_ZERO)
            method = validated_data.get("method", None)
            method_reference = validated_data.get("method_reference", "")

            user = self.context.get("request").user
            validated_data["entry_by"] = user
            validated_data["organization"] = user.organization

            # Validate payment amount
            if amount == DECIMAL_ZERO:
                raise ValidationError(
                    {
                        "detail": "Please provide payment amount."
                    }
                )

            # Validate payment method
            if amount > DECIMAL_ZERO and method is None:
                raise ValidationError(
                    {
                        "detail": "Please provide payment method."
                    }
                )

            # Validate reference for specific payment methods
            if (
                    method
                    and method in (
                    ProcurePaymentMethod.CHEQUE,
                    ProcurePaymentMethod.BKASH,
                    ProcurePaymentMethod.NAGAD)
                    and method_reference == ""
            ):
                raise ValidationError(
                    {"detail": "For CHEQUE, BKASH, and NAGAD, a reference number is mandatory."}
                )

            # Ensure the payment amount does not exceed open credit balance
            if amount > procure.open_credit_balance:
                raise ValidationError(
                    {"detail": "Amount can't be greater than the open credit balance"}
                )

            # Ensure the total paid amount does not exceed the credit amount
            total_paid_amount = procure.paid_amount + amount
            if total_paid_amount > procure.credit_amount:
                raise ValidationError(
                    {"detail": "Amount can't be greater than the credit amount"}
                )

            # Update the payment record
            instance = super().update(instance, validated_data)

            # Update Procure paid amount and open credit balance
            calculate_procure_payment_data(procure)

            return instance

    class Detail(ListSerializer):
        procure = ProcureModelSerializer.Lite(read_only=True)

        class Meta(ProcurePaymentMeta):
            fields = ProcurePaymentMeta.fields + (
                "amount",
                "method",
                "method_reference"
            )
            read_only_fields = ProcurePaymentMeta.read_only_fields + ()
