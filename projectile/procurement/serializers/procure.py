import decimal

from django.db import transaction
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from common.enums import Status, ActionType
from core.serializers import (
    PersonOrganizationLiteSerializer,
)

from ..models import Procure, ProcureItem, ProcurePayment, ProcureGroup
from ..utils import calculate_procurement_procure_data, calculate_procure_payment_data
from procurement.enums import ProcurePaymentMethod


DECIMAL_ZERO = decimal.Decimal("0.000")


class ProcureGroupLiteSerializerForProcure(serializers.ModelSerializer):
    class Meta:
        model = ProcureGroup
        fields = [
            "id",
            "alias",
            "date",
        ]


class ProcurePaymentLiteSerializer(serializers.ModelSerializer):
    """This lite serializer will be used in procure details endpoint to show
    procure related payments, we can't import our existing payment serializer due to circular import.
    """
    class Meta:
        model = ProcurePayment
        fields = (
            "id",
            "alias",
            "date",
            "amount",
            "method",
            "method_reference",
        )
        read_only_fields = (
            "id",
            "alias",
        )


class ProcureMeta(ListSerializer.Meta):
    model = Procure
    fields = ListSerializer.Meta.fields + (
        'id',
        'alias',
        'date',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class ProcureCreditSerializer(serializers.ModelSerializer):
    alias = serializers.UUIDField()
    class Meta():
        model = Procure
        fields = ["alias", "credit_amount"]
        extra_kwargs = {
            "alias": {"required": True, "write_only": True},
            "credit_amount": {"required": True, "write_only": True},
        }

    def validate_credit_amount(self, value):
        if value < 0:
            raise ValidationError("Ensure this value is greater than or equal to 0.")
        return value


class ProcureModelSerializer:

    class List(ListSerializer):
        supplier = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=('id', 'alias', 'company_name', 'phone', 'code')
        )
        contractor = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=('id', 'alias', 'first_name', 'last_name', 'company_name', 'phone', 'code')
        )
        employee = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=('id', 'alias', 'first_name', 'last_name', 'phone',)
        )
        procure_group = ProcureGroupLiteSerializerForProcure(read_only=True)
        is_procure_date_advanced = serializers.BooleanField(read_only=True)

        class Meta(ProcureMeta):
            fields = ProcureMeta.fields + (
                'supplier',
                'contractor',
                'employee',
                'requisition',
                'procure_group',
                'sub_total',
                'discount',
                'operation_start',
                'operation_end',
                'remarks',
                'invoices',
                'estimated_collection_time',
                'current_status',
                'medium',
                # 'geo_location_data',
                "credit_amount",
                "paid_amount",
                "is_credit_purchase",
                "credit_payment_term",
                "credit_payment_term_date",
                "credit_cost_percentage",
                "credit_cost_amount",
                "open_credit_balance",
                "is_procure_date_advanced",
            )
            read_only_fields = ProcureMeta.read_only_fields + ()

    class ProductWiseReport(ListSerializer):
        supplier = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=('id', 'alias', 'company_name', 'phone',)
        )
        employee = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=('id', 'alias', 'first_name', 'last_name', 'phone',)
        )

        class Meta(ProcureMeta):
            fields = ProcureMeta.fields + (
                'supplier',
                'employee',
            )
            read_only_fields = ProcureMeta.read_only_fields + ()


    class Post(ListSerializer):
        from procurement.serializers.procure_item import ProcureItemModelSerializer

        procure_items = ProcureItemModelSerializer.Post(many=True)
        credit_payment_term_date = serializers.DateTimeField(read_only=True)
        credit_cost_amount = serializers.DecimalField(read_only=True, max_digits=19, decimal_places=3)
        open_credit_balance = serializers.DecimalField(read_only=True, max_digits=19, decimal_places=3)
        # Fields for procure payment related data
        payment_amount = serializers.DecimalField(
            max_digits=19,
            decimal_places=3,
            allow_null=True,
            required=False,
            write_only=True,
        )
        payment_method = serializers.ChoiceField(
            allow_blank=True,
            required=False,
            write_only=True,
            choices=ProcurePaymentMethod.choices,
        )
        payment_method_reference = serializers.CharField(
            allow_blank=True,
            required=False,
            write_only=True,
        )

        class Meta(ProcureMeta):
            fields = ProcureMeta.fields + (
                'supplier',
                'contractor',
                'employee',
                'sub_total',
                'discount',
                'operation_start',
                'operation_end',
                'remarks',
                'invoices',
                'copied_from',
                'geo_location_data',
                'procure_items',
                'status',
                'estimated_collection_time',
                'medium',
                'shop_name',
                "credit_amount",
                "paid_amount",
                "is_credit_purchase",
                "credit_payment_term",
                "credit_cost_percentage",
                "credit_payment_term_date",
                "credit_cost_amount",
                "open_credit_balance",
                "payment_amount",
                "payment_method",
                "payment_method_reference",
            )
            read_only_fields = ProcureMeta.read_only_fields + (
            )

        def validate_credit_amount(self, value):
            if self.instance and self.instance.sub_total:
                old_sub_total = self.instance.sub_total
            else:
                old_sub_total = DECIMAL_ZERO

            _credit_amount = value
            _sub_total = decimal.Decimal(self.initial_data.get("sub_total", old_sub_total))

            if _credit_amount and _credit_amount > _sub_total:
                raise serializers.ValidationError({"detail": "Credit amount can not be greater than sub total"})
            return value

        def validate_status(self, value):
            if self.instance.procure_group_id and value == Status.INACTIVE:
                raise serializers.ValidationError("You can't delete the purchase as it is already grouped.")
            return value

        def validate_payment_amount(self, value):
            payment_amount = value
            payment_method = self.initial_data.get("payment_method", "")
            payment_method_reference = self.initial_data.get("payment_method_reference", "")
            if payment_amount and not payment_method:
                raise serializers.ValidationError({"detail": "For making payment, method is required"})

            # Validate reference for specific payment methods
            if (
                    payment_method
                    and payment_method in (
                    ProcurePaymentMethod.CHEQUE,
                    ProcurePaymentMethod.BKASH,
                    ProcurePaymentMethod.NAGAD)
                    and payment_method_reference == ""
            ):
                raise serializers.ValidationError(
                    {"detail": "For CHEQUE, BKASH, and NAGAD, a reference number is mandatory."}
                )

            credit_amount = self.initial_data.get("credit_amount", DECIMAL_ZERO)
            credit_amount = decimal.Decimal(credit_amount)
            if payment_amount > credit_amount:
                raise serializers.ValidationError({"detail": "Payment amount can't be greater than credit amount"})

            return value


        @transaction.atomic
        def create(self, validated_data):
            from pharmacy.helpers import get_product_short_name
            from ..models import PredictionItem

            request = self.context.get("request")

            # check if prediction item is locked for non admin users
            # checking the first prediction item as for all procure items prediction item is same
            is_credit_purchase = validated_data.get("is_credit_purchase", False)
            prediction_item = validated_data.get('procure_items')[0]["prediction_item"]
            is_locked = PredictionItem().get_all_actives().get(id=prediction_item.id).purchase_prediction.is_locked
            if is_locked and not request.user.is_admin_or_super_admin_or_procurement_manager_or_procurement_coordinator():
                raise serializers.ValidationError("You don't have permission to purchases locked procure.")

            copied_from = validated_data.get('copied_from', None)
            if copied_from:
                if copied_from.status == Status.INACTIVE:
                    raise serializers.ValidationError("You can't update the purchase as it doesn't exists.")
                elif copied_from.procure_group is not None:
                    if not (
                            is_credit_purchase
                            or validated_data.get("credit_amount", None) is not None
                            or validated_data.get("credit_payment_term", None) is not None
                            or validated_data.get("credit_cost_percentage", None) is not None
                            or validated_data.get("credit_payment_term_date", None) is not None
                            or validated_data.get("credit_cost_amount", None) is not None
                    ):
                        raise serializers.ValidationError("You can't update the purchase as it is already grouped.")
                else:
                    pass

            # get the procure payment information
            payment_amount = validated_data.pop("payment_amount", None)
            payment_method = validated_data.pop("payment_method", None)
            payment_method_reference = validated_data.pop("payment_method_reference", None)

            entry_by_user_id = request.user.id
            updated_by_user_id = None
            # Change entry by and updated by for edit
            if copied_from:
                entry_by_user_id = copied_from.entry_by_id
                updated_by_user_id = request.user.id
                validated_data['entry_by_id'] = entry_by_user_id
                validated_data['updated_by_id'] = updated_by_user_id

            procure_items = validated_data.pop('procure_items')
            # Check duplicate
            _date = self.initial_data.get("date", "")
            _employee_id = self.initial_data.get("employee", "")
            _invoices = self.initial_data.get("invoices", "")
            _supplier_id = self.initial_data.get("supplier", "")
            # Check for request user tagged contractor availability
            _contractor_id = request.user.tagged_contractor_id if request.user.has_tagged_contractor else None
            _medium = self.initial_data.get("medium", "")
            existing_procure = Procure.objects.filter(
                status=Status.ACTIVE,
                date=_date,
                employee_id=_employee_id,
                invoices=_invoices,
                supplier_id=_supplier_id,
                contractor_id=_contractor_id,
                medium=_medium,
            )
            if existing_procure.exists():
                return existing_procure.first()

            if not is_credit_purchase:
                validated_data["credit_payment_term"] = 0
                validated_data["credit_payment_term_date"] = None
                validated_data["credit_cost_percentage"] = DECIMAL_ZERO
                validated_data["credit_cost_amount"] = DECIMAL_ZERO
                validated_data["open_credit_balance"] = DECIMAL_ZERO
                validated_data["credit_amount"] = DECIMAL_ZERO
                validated_data["paid_amount"] = DECIMAL_ZERO

            procure_instance = Procure.objects.create(
                **validated_data,
                contractor_id=_contractor_id,
            )

            # This function will calculate credit_payment_term_date, credit_cost_amount, open_credit_balance
            calculate_procurement_procure_data(procure_instance)

            for item in procure_items:
                stock = item.get('stock')
                product_full_name = get_product_short_name(stock.product)
                item['procure'] = procure_instance
                item['product_name'] = product_full_name
                item['organization_id'] = request.user.organization_id
                item['entry_by_id'] = entry_by_user_id
                item['updated_by_id'] = updated_by_user_id
                procure_item = ProcureItem.objects.create(
                    **item
                )
            # Inactive old instance for edit
            if procure_instance.copied_from_id:
                procure_instance.copied_from.status = Status.INACTIVE
                procure_instance.copied_from.save(update_fields=['status',])

            # Create a payment for the procure if payment available
            if payment_amount and is_credit_purchase:
                procure_payment = ProcurePayment.objects.create(
                    date=timezone.now(),
                    amount=payment_amount,
                    method=payment_method,
                    method_reference=payment_method_reference or "",
                    procure_id=procure_instance.id,
                    organization_id=request.user.organization_id,
                    entry_by_id=request.user.id,
                )

            # Calculate procure payment data
            procure_instance = calculate_procure_payment_data(procure_instance)

            return procure_instance

        def update(self, instance, validated_data):
            # get the procure payment information
            payment_amount = validated_data.pop("payment_amount", None)
            payment_method = validated_data.pop("payment_method", None)
            payment_method_reference = validated_data.pop("payment_method_reference", None)
            procure_items = validated_data.pop('procure_items', None)
            credit_payment_term = validated_data.get('credit_payment_term', None)

            if credit_payment_term == 0:
                raise serializers.ValidationError({
                    "detail": "credit payment term value 0 is not acceptable"
                })


            # Get the 'credit_amount' from the validated data.
            credit_amount = validated_data.get("credit_amount", None)
            # Get the 'paid_amount' from the instance.
            paid_amount = instance.paid_amount

            # Check if credit amount is provided and less than the paid amount, if so, raise a validation error.
            if (credit_amount or credit_amount == DECIMAL_ZERO) and credit_amount < paid_amount:
                raise serializers.ValidationError(
                    {
                        "detail": f"Credit amount can not be less than paid amount, already paid BDT - {paid_amount}."
                    }
                )

            procure_instance = super().update(instance=instance, validated_data=validated_data)

            # This function will calculate credit_payment_term_date, credit_cost_amount, open_credit_balance
            calculate_procurement_procure_data(procure_instance)

            # Calculate procure payment data
            procure_instance = calculate_procure_payment_data(procure_instance)

            return procure_instance

    class Details(ListSerializer):
        from procurement.serializers.procure_item import ProcureItemModelSerializer

        supplier = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=('id', 'alias', 'company_name', 'phone', 'code', 'contact_person_number', 'contact_person_address',)
        )
        contractor = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=('id', 'alias', 'company_name', 'phone', 'code', 'contact_person_number', 'contact_person_address',)
        )
        employee = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=('id', 'alias', 'first_name', 'last_name', 'phone',)
        )
        procure_items = ProcureItemModelSerializer.Details(many=True)
        procure_payments = ProcurePaymentLiteSerializer(many=True, read_only=True)

        class Meta(ProcureMeta):
            fields = ProcureMeta.fields + (
                'supplier',
                'contractor',
                'employee',
                'requisition',
                'sub_total',
                'discount',
                'operation_start',
                'operation_end',
                'remarks',
                'invoices',
                'geo_location_data',
                'procure_items',
                "procure_group",
                'estimated_collection_time',
                'current_status',
                'medium',
                'shop_name',
                "credit_amount",
                "paid_amount",
                "is_credit_purchase",
                "credit_payment_term",
                "credit_payment_term_date",
                "credit_cost_percentage",
                "open_credit_balance",
                "procure_payments",
            )
            read_only_fields = ProcureMeta.read_only_fields + ()

    class ProcurePurchase(serializers.Serializer):
        procure = serializers.PrimaryKeyRelatedField(
            queryset=Procure.objects.filter(
                status=Status.ACTIVE
            ),
            required=True
        )
        action = serializers.ChoiceField(choices=ActionType().choices(), required=True)
        date = serializers.DateTimeField(required=True)

    class ProcureItemsOnly(ListSerializer):
        from procurement.serializers.procure_item import ProcureItemModelSerializer

        procure_items = ProcureItemModelSerializer.Details(many=True)

        class Meta(ProcureMeta):
            fields = ProcureMeta.fields + (
                "sub_total",
                "is_credit_purchase",
                "credit_payment_term",
                "credit_payment_term_date",
                "credit_amount",
                "paid_amount",
                "open_credit_balance",
                "procure_items",
            )
            read_only_fields = ProcureMeta.read_only_fields + ()

    class Lite(ListSerializer):
        """This serializer will be used in procure returns."""

        class Meta(ProcureMeta):
            fields = ProcureMeta.fields + (
            )
            read_only_fields = ProcureMeta.read_only_fields + (
            )

    class ProcureCreditBulkUpdate(serializers.ModelSerializer):
        """
        This serializer will be used for procure credit bulk update.
        """

        procures = serializers.ListField(child=ProcureCreditSerializer(), allow_empty=False, write_only=True)

        class Meta():
            model = Procure
            fields = ["procures", "credit_payment_term", "credit_cost_percentage"]
            extra_kwargs = {
                "credit_payment_term": {"required": True, "write_only": True},
                "credit_cost_percentage": {"required": True, "write_only": True},
            }

        def validate_credit_cost_percentage(self, value):
            if value < 0 or value > 100:
                raise ValidationError("Ensure this value is within 0 to 100.")
            return value
