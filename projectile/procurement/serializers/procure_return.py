"""Serializers for Procure Returns."""
from django.db import transaction
from django.db.models import Sum, Value, fields
from django.db.models.functions import Coalesce
from django.utils import timezone

from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer

from core.custom_serializer.person_organization import PersonOrganizationBaseSerializer

from procurement.enums import ReturnSettlementMethod, ReturnCurrentStatus
from procurement.models import ProcureReturn, ReturnSettlement, ProcureItem
from procurement.utils import calculate_total_settled_amount

from procurement.serializers.procure import ProcureModelSerializer
from procurement.serializers.procure_return_settlement import ReturnSettlementModelSerializer


DECIMAL_ZERO = 0.00

class ProcurePurchaseListProductContractorWiseSerializer(serializers.ModelSerializer):
    stock_id = serializers.IntegerField()
    procure_id = serializers.IntegerField()
    total_quantity = serializers.FloatField()
    total_return_quantity = serializers.DecimalField(max_digits=19, decimal_places=3)

    class Meta:
        model = ProcureItem
        fields = [
            "date",
            "rate",
            "procure_id",
            "stock_id",
            "product_name",
            "company_name",
            "total_quantity",
            "total_return_quantity",
        ]


class ProcureReturnMeta(ListSerializer.Meta):
    model = ProcureReturn
    fields = ListSerializer.Meta.fields + (
        "status",
        "date",
        "reason",
        "reason_note",
        "stock",
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + ()


class ReturnSettlementLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnSettlement
        fields = ("settlement_method", "settlement_method_reference")


class ProcureReturnModelSerializer:
    class List(ListSerializer):
        procure = ProcureModelSerializer.Lite(read_only=True)
        contractor = PersonOrganizationBaseSerializer.MinimalList(read_only=True)
        employee = PersonOrganizationBaseSerializer.MinimalList(read_only=True)
        return_settlement = ReturnSettlementLiteSerializer(
            source="procure_return_settlements",
            read_only=True,
            many=True,
        )

        class Meta(ProcureReturnMeta):
            fields = ProcureReturnMeta.fields + (
                "procure",
                "contractor",
                "current_status",
                "full_settlement_date",
                "product_name",
                "quantity",
                "rate",
                "total_return_amount",
                "total_settled_amount",
                "employee",
                "return_settlement"
            )
            read_only_fields = ListSerializer.Meta.read_only_fields + ()

    class Post(ListSerializer):
        settlement_method_reference = serializers.CharField(
            allow_blank=True, required=False, write_only=True
        )
        return_amount = serializers.DecimalField(
            max_digits=19,
            decimal_places=3,
            allow_null=True,
            required=False,
            write_only=True,
        )
        is_fully_settled = serializers.BooleanField(
            default=False,
            required=False,
            write_only=True
        )

        class Meta(ProcureReturnMeta):
            fields = ProcureReturnMeta.fields + (
                "procure",
                "settlement_method",
                "settlement_method_reference",
                "quantity",
                "return_amount",
                "is_fully_settled"
            )
            read_only_fields = ProcureReturnMeta.read_only_fields + ()

        @transaction.atomic
        def create(self, validated_data):

            user = self.context.get("request").user
            # Get employee id for the request user
            employee_id = user.get_person_organization_for_employee(pk_only=True)
            settlement_method = validated_data.get("settlement_method", None)
            settlement_method_reference = validated_data.pop(
                "settlement_method_reference", None
            )
            return_amount = validated_data.pop("return_amount", None)
            is_fully_settled = validated_data.pop("is_fully_settled", None)

             # Validation for fully_settled return settlement method existance
            if is_fully_settled and not settlement_method:
                raise serializers.ValidationError(
                    {"detail": "For fully settled procure return settlement method is required."}
                )

            procure = validated_data.get("procure", None)
            stock = validated_data.get("stock", None)
            if stock is None:
                raise serializers.ValidationError(
                    {"detail": "Stock id is required to create procure return."}
                )
            # Check if return item is available for the same procure and stock
            existing_procure_return = ProcureReturn().get_all_actives().filter(
                procure_id=procure.id,
                stock_id=stock.id,
            ).aggregate(
                old_return_quantity=Coalesce(Sum("quantity"), Value(DECIMAL_ZERO), output_field=fields.DecimalField())
            )
            old_return_quantity = existing_procure_return.get("old_return_quantity", DECIMAL_ZERO)

            procure_item = (
                ProcureItem().get_all_actives().filter(stock_id=stock.id, procure_id=procure.id)
                .only("rate", "quantity")
                .first()
            )

            procure_item_rate = procure_item.rate or DECIMAL_ZERO
            procure_item_quantity = procure_item.quantity or DECIMAL_ZERO
            return_quantity = validated_data.get("quantity", DECIMAL_ZERO)
            # Validate that the return quantity is greater than 0
            if return_quantity < 1:
                raise serializers.ValidationError(
                    {"detail": "Return Quantity should be greater than 0."}
                )

            total_return_quantity = old_return_quantity + return_quantity

            # Validate that the total return quantity is not greater than the purchase quantity
            if total_return_quantity > procure_item_quantity:
                raise serializers.ValidationError(
                    {"detail": "Return quantity is greater than purchase quantity."}
                )
            procure_item_total_return_amount = procure_item_rate * return_quantity
            # Validation for Cheque settlement cause cheque number is required for check settlement
            if (
                settlement_method
                and settlement_method == ReturnSettlementMethod.CHEQUE
                and not settlement_method_reference
            ):
                raise serializers.ValidationError(
                    {"detail": "For cheque settlement, cheque number is mandatory."}
                )
            # Validate that cheque or cash settlement includes a return amount
            if (
                settlement_method
                and settlement_method
                in (ReturnSettlementMethod.CASH, ReturnSettlementMethod.CHEQUE)
                and (return_amount is None or return_amount<1)
            ):
                raise serializers.ValidationError(
                    {
                        "detail": "Please provide return amount for cheque or cash settlement."
                    }
                )
            # Ensure that the return amount is not greater than the total return amount
            if return_amount and return_amount > procure_item_total_return_amount:
                raise serializers.ValidationError({"detail": "Return amount is greater than total_return_amount"})

            # Create a procure return instance
            validated_data["product_name"] = stock.product.form.name + " " + stock.product_full_name
            validated_data["contractor_id"] = procure.contractor_id
            validated_data["employee_id"] = employee_id
            validated_data["rate"] = procure_item_rate
            validated_data["total_return_amount"] = procure_item_total_return_amount

            if (settlement_method == ReturnSettlementMethod.NET_AGAINST_COMMISSION or
                    settlement_method == ReturnSettlementMethod.PRODUCT_REPLACEMENT or
                    is_fully_settled is not False):
                validated_data["current_status"] = ReturnCurrentStatus.SETTLED
                validated_data["full_settlement_date"] = timezone.now()
                validated_data["total_settled_amount"] = procure_item_total_return_amount

                # update the return amount for the above case
                return_amount = procure_item_total_return_amount

            procure_return = super().create(validated_data)

            # If a settlement method is specified, create a return settlement instance
            if settlement_method:
                ReturnSettlement.objects.create(
                    procure_return_id=procure_return.id,
                    date=procure_return.date,
                    settlement_method=settlement_method,
                    settlement_method_reference=settlement_method_reference or "",
                    amount=return_amount if return_amount else DECIMAL_ZERO,
                    employee_id=employee_id,
                    entry_by_id=user.id,
                )

            # Update the current status and total settled amount for the procure return if not fully settled
            if not (settlement_method == ReturnSettlementMethod.NET_AGAINST_COMMISSION or
                    settlement_method == ReturnSettlementMethod.PRODUCT_REPLACEMENT or
                    is_fully_settled is not False):
                procure_return = calculate_total_settled_amount(
                    procure_return=procure_return
                )

            return procure_return

    class Detail(ListSerializer):
        settlement_method_reference = serializers.CharField(
            allow_blank=True, required=False, write_only=True
        )
        return_amount = serializers.DecimalField(
            max_digits=19,
            decimal_places=3,
            allow_null=True,
            required=False,
            write_only=True,
        )
        is_fully_settled = serializers.BooleanField(
            default=False,
            required=False,
            write_only=True
        )

        class Meta(ProcureReturnMeta):
            fields = ProcureReturnMeta.fields + (
                "procure",
                "settlement_method",
                "settlement_method_reference",
                "quantity",
                "return_amount",
                "is_fully_settled"
            )
            read_only_fields = ProcureReturnMeta.read_only_fields + ()

        @transaction.atomic
        def update(self, instance, validated_data):
            user = self.context.get("request").user
            settlement_method = validated_data.get("settlement_method", None)
            settlement_method_reference = validated_data.pop(
                "settlement_method_reference", None
            )
            return_amount = validated_data.pop("return_amount", None)
            is_fully_settled = validated_data.pop("is_fully_settled", None)
            quantity = validated_data.get("quantity", None)

            # Validation for zero quantity
            if quantity is not None and quantity == 0:
                raise serializers.ValidationError({"detail": "Return quantity should be greater than zero."})
            # Validate that return quantity does not exceed purchase quantity
            if quantity:
                procure_item = (
                    ProcureItem().get_all_actives().filter(procure_id=instance.procure_id, stock_id=instance.stock_id)
                    .only("rate", "quantity")
                    .first()
                )
                # get total reutrn item for that procure
                exsting_return_quantity = ProcureReturn().get_all_actives().filter(
                    procure_id=instance.procure_id,stock_id=instance.stock_id
                ).exclude(id=instance.id).aggregate(
                    old_return_quantity=Coalesce(Sum("quantity"), Value(DECIMAL_ZERO), output_field=fields.DecimalField())
                )
                old_return_quantity = exsting_return_quantity.get("old_return_quantity", DECIMAL_ZERO)
                total_return_quantity = old_return_quantity + quantity

                if total_return_quantity > procure_item.quantity:
                    raise serializers.ValidationError({"detail": "Return quantity is greater than purchase quantity."})

            # Check If this Procure Return already settled
            if instance.current_status == ReturnCurrentStatus.SETTLED:
                raise serializers.ValidationError(
                    {
                        "detail": "This procure return already settled."
                    }
                )
            if return_amount and settlement_method is None:
                raise serializers.ValidationError(
                    {
                        "detail": "Please provide settlement method"
                    }
                )
            # if user provides PRODUCT_REPLACEMENT or NET_AGAINST_COMMISSION then set as fully settled
            if (
                    settlement_method and
                    settlement_method == ReturnSettlementMethod.PRODUCT_REPLACEMENT or
                    settlement_method == ReturnSettlementMethod.NET_AGAINST_COMMISSION or
                    is_fully_settled
                ):
                instance.current_status = ReturnCurrentStatus.SETTLED
                return_amount = instance.total_return_amount - instance.total_settled_amount
                instance.full_settlement_date = timezone.now()

            if (
                settlement_method
                and settlement_method == ReturnSettlementMethod.CHEQUE
                and not settlement_method_reference
            ):
                raise serializers.ValidationError(
                    {"detail": "For cheque settlement, cheque number is mandatory."}
                )
            # Validation for Cheque or cash settlement
            if (
                settlement_method
                and settlement_method
                in (ReturnSettlementMethod.CASH, ReturnSettlementMethod.CHEQUE)
                and return_amount is None
            ):
                raise serializers.ValidationError(
                    {
                        "detail": "Please provide return amount for cheque or cash settlement."
                    }
                )

            instance.updated_by_id = user.id
            super().update(instance, validated_data)

            if settlement_method:
                ReturnSettlement.objects.create(
                    procure_return_id=instance.id,
                    date=instance.date,
                    settlement_method=settlement_method,
                    settlement_method_reference=settlement_method_reference or "",
                    amount=return_amount if return_amount else DECIMAL_ZERO,
                    employee_id=instance.employee_id,
                    entry_by_id=user.id,
                )

            # Update the return current Status and total_settled_amount
            procure_return = calculate_total_settled_amount(
                procure_return=instance
            )

            return procure_return
