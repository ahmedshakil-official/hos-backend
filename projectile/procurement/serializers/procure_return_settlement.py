"""Serializers for Procure Returns Settlements."""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.db.models.functions import Coalesce
from django.db.models import DecimalField, Sum, Value

from rest_framework import serializers
from rest_framework.validators import ValidationError
from rest_framework.serializers import SlugRelatedField
from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer

from core.custom_serializer.person_organization import PersonOrganizationBaseSerializer
from core.models import PersonOrganization

from procurement.models import ReturnSettlement, ProcureReturn, ProcureItem
from procurement.utils import calculate_total_settled_amount
from procurement.enums import ReturnCurrentStatus, ReturnSettlementMethod

DECIMAL_ZERO = Decimal('0.00')


class ReturnSettlementMeta(ListSerializer.Meta):
    model = ReturnSettlement
    fields = ListSerializer.Meta.fields + (
        "date",
        "procure_return",
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + ("procure_return",)


class ReturnSettlementModelSerializer:
    class List(ListSerializer):
        employee = PersonOrganizationBaseSerializer.MinimalList(read_only=True)
        product_name = serializers.CharField(read_only=True)
        quantity = serializers.DecimalField(max_digits=19, decimal_places= 3, read_only=True)
        is_fully_settled = serializers.BooleanField(
            default=False,
            required=False,
            write_only=True
        )

        class Meta(ReturnSettlementMeta):
            fields = ReturnSettlementMeta.fields + (
                "status",
                "employee",
                "settlement_method",
                "settlement_method_reference",
                "amount",
                "product_name",
                "quantity",
                "is_fully_settled"
            )
            read_only_fields = ListSerializer.Meta.read_only_fields + ()

        def update(self, instance, validated_data):
            """
            Updates a settlement with the provided data.

            Args:
                instance (Settlement): The settlement instance to update.
                validated_data (dict): Validated data containing settlement information.

            Raises:
                ValidationError: If certain conditions are not met, exceptions are raised with details.

            Returns:
                Settlement: The updated settlement instance.

            """
            settlement_method = validated_data.get("settlement_method", None)
            amount = validated_data.get("amount", DECIMAL_ZERO)

            # For settling by cheque, the cheque number/settlement reference is mandatory
            settlement_method_reference = validated_data.get(
                "settlement_method_reference", None
            )
            is_fully_settled = validated_data.pop("is_fully_settled", None)

            procure_item = (
                ProcureItem().get_all_actives().filter(
                    stock_id=instance.procure_return.stock.id, procure_id=instance.procure_return.procure.id
                ).only("rate", "quantity")
                .first()
            )

            procure_item_rate = procure_item.rate or DECIMAL_ZERO
            procure_item_total_return_amount = procure_item_rate * instance.procure_return.quantity

            if amount > DECIMAL_ZERO and settlement_method is None:
                raise ValidationError(
                    {
                        "detail": "Please provide settlement method."
                    }
                )

            if (
                settlement_method
                and settlement_method == ReturnSettlementMethod.CHEQUE
                and not settlement_method_reference
            ):
                raise ValidationError(
                    {"detail": "For cheque settlement, cheque number is mandatory."}
                )

            if (
                settlement_method
                and settlement_method
                in (ReturnSettlementMethod.CASH, ReturnSettlementMethod.CHEQUE)
                and amount is DECIMAL_ZERO
            ):
                raise ValidationError(
                    {
                        "detail": "Please provide return amount for cheque or cash settlement."
                    }
                )

            total_settled_amount = instance.procure_return.total_settled_amount + (amount - instance.amount)
            if total_settled_amount > instance.procure_return.total_return_amount:
                raise ValidationError(
                    {
                        "detail": "Return amount is greater than total return amount."
                    }
                )

            if (settlement_method == ReturnSettlementMethod.NET_AGAINST_COMMISSION or
                    settlement_method == ReturnSettlementMethod.PRODUCT_REPLACEMENT or
                    is_fully_settled is not False):

                old_settled_amount = instance.procure_return.total_settled_amount

                instance.procure_return.current_status = ReturnCurrentStatus.SETTLED
                instance.procure_return.full_settlement_date = timezone.now()
                instance.procure_return.total_settled_amount = procure_item_total_return_amount

                validated_data["amount"] = (
                        instance.procure_return.total_return_amount - old_settled_amount
                )

                instance.procure_return.save(
                    update_fields=[
                        "current_status",
                        "full_settlement_date",
                        "total_settled_amount"
                    ]
                )
            validated_data["amount"] = amount
            # Call the parent class's update method to perform the actual update
            instance = super().update(instance, validated_data)

            # calculate_total_settled_amount handles the return update for settlement and return
            calculate_total_settled_amount(instance.procure_return)

            return instance

    class Post(ListSerializer):
        procure_return = SlugRelatedField(
            queryset=ProcureReturn().get_all_non_inactives(),
            slug_field="alias",
            error_messages={
                "detail": "Procure return does not exist.",
            },
            write_only=True
        )
        is_fully_settled = serializers.BooleanField(
            default=False,
            required=False,
            write_only=True
        )

        class Meta(ReturnSettlementMeta):
            fields = ReturnSettlementMeta.fields + (
                "settlement_method",
                "settlement_method_reference",
                "amount",
                "is_fully_settled"
            )
            read_only_fields = ListSerializer.Meta.read_only_fields + ()

        @transaction.atomic
        def create(self, validated_data):
            # get employee id [Person Organization] from current user
            employee_id = self.context.get("request").user.get_person_organization_for_employee(pk_only=True)

            settlement_method = validated_data.get("settlement_method", None)
            settlement_method_reference = validated_data.get(
                "settlement_method_reference", None
            )
            amount = validated_data.get("amount", None)
            procure_return: ProcureReturn = validated_data.get("procure_return", None)

            # get person organization and set to validated_data in employee
            validated_data["employee_id"] = employee_id
            is_fully_settled = validated_data.pop("is_fully_settled", None)

            if procure_return.current_status == ReturnCurrentStatus.SETTLED:
                raise ValidationError(
                    {"detail": "procure return already Settled"}
                )

            procure_item = (
                ProcureItem().get_all_actives().filter(
                    stock_id=procure_return.stock.id, procure_id=procure_return.procure.id
                ).only("rate", "quantity")
                .first()
            )

            procure_item_rate = procure_item.rate or DECIMAL_ZERO
            procure_item_total_return_amount = procure_item_rate * procure_return.quantity

            if amount and settlement_method is None:
                raise ValidationError(
                    {
                        "detail": "Please provide settlement method."
                    }
                )

            if (
                settlement_method
                and settlement_method == ReturnSettlementMethod.CHEQUE
                and not settlement_method_reference
            ):
                raise ValidationError(
                    {"detail": "For cheque settlement, cheque number is mandatory."}
                )

            if (
                settlement_method
                and settlement_method
                in (ReturnSettlementMethod.CASH, ReturnSettlementMethod.CHEQUE)
                and (amount is None or amount < 1)
            ):
                raise ValidationError(
                    {
                        "detail": "Please provide return amount for cheque or cash settlement."
                    }
                )

            total_settled_amount = procure_return.total_settled_amount + amount
            if procure_return.total_return_amount < total_settled_amount:
                raise ValidationError(
                    {
                        "detail": "Return amount is greater than total return amount."
                    }
                )

            if (settlement_method == ReturnSettlementMethod.NET_AGAINST_COMMISSION or
                    settlement_method == ReturnSettlementMethod.PRODUCT_REPLACEMENT or
                    is_fully_settled is not False):

                old_settled_amount = procure_return.total_settled_amount

                procure_return.current_status = ReturnCurrentStatus.SETTLED
                procure_return.full_settlement_date = timezone.now()
                procure_return.total_settled_amount = procure_item_total_return_amount

                validated_data["amount"] = procure_return.total_return_amount - old_settled_amount

                procure_return.save(
                    update_fields=[
                        "current_status",
                        "full_settlement_date",
                        "total_settled_amount"
                    ]
                )

            instance = super().create(validated_data=validated_data)

            if not (settlement_method == ReturnSettlementMethod.NET_AGAINST_COMMISSION or
                    settlement_method == ReturnSettlementMethod.PRODUCT_REPLACEMENT or
                    is_fully_settled is not False):

                # Update Procure Return status and amount
                calculate_total_settled_amount(
                    procure_return=procure_return
                )

            return instance
