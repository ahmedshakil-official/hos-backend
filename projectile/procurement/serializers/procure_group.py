import decimal
import time
from datetime import datetime
from dotmap import DotMap

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer
from common.enums import Status, ActionType
from common.utils import get_item_from_list_of_dict, get_item_from_list_of_dict_v2
from core.serializers import PersonOrganizationLiteSerializer
from procurement.enums import ProcurePaymentMethod
from procurement.models import ProcureGroup, Procure, ProcurePayment
from procurement.serializers.procure import ProcureModelSerializer
from procurement.serializers.procure_item import ProcureItemModelSerializer
from procurement.utils import calculate_procurement_procure_group_data, calculate_procure_group_payment_data

DECIMAL_ZERO = decimal.Decimal("0.000")


class ProcureGroupMeta(ListSerializer.Meta):
    model = ProcureGroup
    fields = ListSerializer.Meta.fields + (
        'id',
        'alias',
        'current_status',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
    )


class ProcureGroupModelSerializer:
    class List(ListSerializer):
        supplier = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=('id', 'alias', 'company_name', 'first_name', 'last_name', 'code')
        )
        contractor = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=("id","alias","company_name", "first_name", "last_name", "code")
        )
        invoices = serializers.ListField(
            read_only=True,
            allow_null=True,
        )
        total_credit_amount = serializers.DecimalField(
            max_digits=19, decimal_places=3, read_only=True,
        )
        total_paid_amount = serializers.DecimalField(
            max_digits=19, decimal_places=3, read_only=True,
        )
        total_open_credit_balance = serializers.DecimalField(
            max_digits=19, decimal_places=3, read_only=True,
        )
        class Meta(ProcureGroupMeta):
            fields = ProcureGroupMeta.fields + (
                'date',
                'status',
                'procure_group_procures',
                'supplier',
                'contractor',
                'invoices',
                'requisition',
                'total_amount',
                'total_discount',
                'num_of_boxes',
                'num_of_unique_boxes',
                "credit_amount",
                "paid_amount",
                "is_credit_purchase",
                "credit_payment_term",
                "credit_payment_term_date",
                "credit_cost_percentage",
                "credit_cost_amount",
                "open_credit_balance",
                "cash_commission",
                "total_credit_amount",
                "total_paid_amount",
                "total_open_credit_balance",

            )
            read_only_fields = ProcureGroupMeta.read_only_fields + ()

    class Post(ListSerializer):
        procure_date = serializers.DateField(
            required=True,
        )

        class Meta(ProcureGroupMeta):
            fields = (
                'procure_date',
            )

        def create(self, validated_data):
            procure_queryset = Procure.objects.filter(
                date__date=validated_data['procure_date'],
                status=Status.ACTIVE,
                procure_group__isnull=True,
            )
            procure_date = validated_data.get("procure_date")
            procure_date = procure_date.strftime("%Y-%m-%d")
            procures = procure_queryset.values("supplier", "contractor").annotate(
                ids=ArrayAgg('id', distinct=True),
                supplier_company_name=F('supplier__company_name'),
                total_amount=Sum('sub_total'),
                total_discount=Sum('discount'),
                current_status_array=ArrayAgg('current_status', distinct=True),
            )
            procure_boxes = list(procure_queryset.values("supplier", "contractor").annotate(
                total_boxes=Sum(
                    'procure_items__quantity',
                    filter=Q(procure_items__status=Status.ACTIVE)
                ),
                total_unique_boxes=Count(
                    'procure_items__stock',
                    distinct=True,
                    filter=Q(procure_items__status=Status.ACTIVE)
                ),
            ))

            created_procure_groups = []
            procure_could_not_be_grouped = []
            for procure in procures:
                if len(procure['current_status_array']) > 1:
                    procure_could_not_be_grouped.append({
                        'supplier': procure['supplier_company_name'],
                        'procure_ids': procure['ids'],
                    })
                    continue
                box_data = DotMap(get_item_from_list_of_dict_v2(
                    procure_boxes,
                    "supplier",
                    procure["supplier"],
                    "contractor",
                    procure["contractor"],
                ))
                instance = ProcureGroup.objects.create(
                    entry_by_id=self.context['request'].user.id,
                    date=procure_date,
                    supplier_id=procure['supplier'],
                    contractor_id=procure['contractor'],
                    total_amount=procure['total_amount'],
                    total_discount=procure['total_discount'],
                    num_of_boxes=box_data.total_boxes,
                    num_of_unique_boxes=box_data.total_unique_boxes,
                    current_status=procure['current_status_array'][0],
                )
                created_procure_groups.append(instance)
                Procure.objects.filter(
                    id__in=procure['ids'],
                ).update(
                    procure_group_id=instance.id,
                )
            return created_procure_groups, procure_could_not_be_grouped

    class Details(ListSerializer):
        supplier = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=(
                'id', 'alias', 'company_name', 'first_name',
                'last_name', 'phone', 'code', 'contact_person_number',
                'contact_person_address'
            )
        )
        procures = ProcureModelSerializer.ProcureItemsOnly(
            many=True,
        )
        invoices = serializers.ListField(
            read_only=True,
            allow_null=True,
        )
        employees = serializers.ListField(
            child=serializers.JSONField(),
            read_only=True,
            allow_null=True,
        )
        payment_amount = serializers.DecimalField(
            default=0.00,
            max_digits=19,
            decimal_places=3,
            write_only=True,
            required=False
        )
        payment_method = serializers.ChoiceField(
            choices=ProcurePaymentMethod.choices,
            default=ProcurePaymentMethod.CASH,
            write_only=True,
            required=False
        )
        payment_method_reference = serializers.CharField(
            max_length=255,
            allow_blank=True,
            write_only=True,
            required=False
        )
        payment_date = serializers.DateTimeField(write_only=True, required=True)
        total_credit_amount = serializers.DecimalField(
            max_digits=19, decimal_places=3, read_only=True,
        )
        total_paid_amount = serializers.DecimalField(
            max_digits=19, decimal_places=3, read_only=True,
        )
        total_open_credit_balance = serializers.DecimalField(
            max_digits=19, decimal_places=3, read_only=True,
        )
        contractor = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=("id", "alias", "company_name", "first_name", "last_name", "code")
        )

        class Meta(ProcureGroupMeta):
            fields = ProcureGroupMeta.fields + (
                'date',
                'status',
                'supplier',
                'employees',
                "contractor",
                'invoices',
                'total_amount',
                'total_discount',
                'num_of_boxes',
                'num_of_unique_boxes',
                'procures',
                "credit_amount",
                "paid_amount",
                "requisition",
                "is_credit_purchase",
                "credit_payment_term",
                "credit_payment_term_date",
                "credit_cost_percentage",
                "credit_cost_amount",
                "open_credit_balance",
                "cash_commission",
                "payment_date",
                "payment_amount",
                "payment_method",
                "payment_method_reference",
                "total_credit_amount",
                "total_paid_amount",
                "total_open_credit_balance",
            )
            read_only_fields = ProcureGroupMeta.read_only_fields + ()


    class Update(ListSerializer):
        payment_amount = serializers.DecimalField(
            default=0.00,
            max_digits=19,
            decimal_places=3,
            write_only=True,
            required=False
        )
        payment_method = serializers.ChoiceField(
            choices=ProcurePaymentMethod.choices,
            default=ProcurePaymentMethod.CASH,
            write_only=True,
            required=False
        )
        payment_method_reference = serializers.CharField(
            max_length=255,
            allow_blank=True,
            write_only=True,
            required=False
        )
        payment_date = serializers.DateTimeField(write_only=True, required=True)

        class Meta(ProcureGroupMeta):
            fields = ProcureGroupMeta.fields + (
                "date",
                "status",
                "supplier",
                "contractor",
                "total_amount",
                "total_discount",
                "num_of_boxes",
                "num_of_unique_boxes",
                "credit_amount",
                "paid_amount",
                "is_credit_purchase",
                "credit_payment_term",
                "credit_payment_term_date",
                "credit_cost_percentage",
                "credit_cost_amount",
                "open_credit_balance",
                "cash_commission",
                "payment_date",
                "payment_amount",
                "payment_method",
                "payment_method_reference",
            )
            read_only_fields = ProcureGroupMeta.read_only_fields + ("total_amount",)

        def validate_credit_amount(self, value):
            if self.instance and self.instance.total_amount:
                old_total_amount = self.instance.total_amount
            else:
                old_total_amount = DECIMAL_ZERO

            _credit_amount = value
            _total_amount = decimal.Decimal(self.initial_data.get("total_amount", old_total_amount))

            if _credit_amount and _credit_amount > _total_amount:
                raise serializers.ValidationError({"detail": "Credit amount can not be greater than total amount"})
            return value


        def update(self, instance, validated_data):
            request = self.context["request"]
            # Get the 'credit_amount' from the validated data.
            credit_amount = validated_data.get("credit_amount", None)
            # Get the 'paid_amount' from the instance.
            paid_amount = instance.paid_amount

            # Get procure group payment fields
            payment_amount = validated_data.pop("payment_amount", None)
            payment_method = validated_data.pop("payment_method", None)
            payment_method_reference = validated_data.pop("payment_method_reference", None)
            payment_date = validated_data.pop("payment_date", None)

            if payment_amount and not payment_method:
                raise serializers.ValidationError({"detail": "For making payment, method is required"})

            if payment_amount and not payment_date:
                raise serializers.ValidationError({"detail": "For making payment, date is required"})

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

            # Ensure the payment amount does not exceed open credit balance
            if payment_amount and payment_amount > instance.open_credit_balance:
                raise ValidationError(
                    {"detail": "Amount can't be greater than the open credit balance"}
                )

            # Check if credit amount is provided and less than the paid amount, if so, raise a validation error.
            if (credit_amount or credit_amount == DECIMAL_ZERO) and credit_amount < paid_amount:
                raise serializers.ValidationError(
                    {
                        "detail": f"Credit amount can not be less than paid amount, already paid BDT - {paid_amount}."
                    }
                )

            procure_group_instance = super().update(instance=instance, validated_data=validated_data)
            # create the payment
            if payment_amount and payment_method and payment_date:
                ProcurePayment.objects.create(
                    date=payment_date,
                    amount=payment_amount,
                    method=payment_method,
                    method_reference=payment_method_reference,
                    procure_group=procure_group_instance,
                    organization_id=request.user.organization_id
                )

            # This function will calculate credit_payment_term_date, credit_cost_amount, open_credit_balance
            calculate_procurement_procure_group_data(procure_group_instance)

            # Calculate procure payment data
            procure_group_instance = calculate_procure_group_payment_data(procure_group_instance)

            return procure_group_instance



    class StatusChange(ListSerializer):
        alias = serializers.CharField(
            required=True,
        )

        class Meta(ProcureGroupMeta):
            fields = (
                'alias',
                'current_status',
            )
            read_only_fields = ProcureGroupMeta.read_only_fields + ()

        def create(self, validated_data):
            current_status = validated_data['current_status']
            procure_group = ProcureGroup.objects.filter(
                alias=validated_data.pop('alias'),
            ).only('current_status')
            if procure_group.exists():
                procure_group = procure_group.first()
                procure_group.current_status = current_status
                procure_group.save(update_fields=['current_status'])
                for procure in procure_group.procure_group_procures.filter(status=Status.ACTIVE):
                    procure.current_status = current_status
                    procure.save(update_fields=['current_status'])
                    procure.procure_status.create(
                        current_status=current_status,
                        entry_by_id=self.context['request'].user.id,
                    )
                return procure_group
            return validated_data

    class CompletePurchase(serializers.Serializer):
        alias = serializers.CharField(
            required=True,
        )
        action = serializers.ChoiceField(choices=ActionType().choices(), required=True)
        date = serializers.DateTimeField(required=True)

    class ProcuresEdit(ListSerializer):
        alias = serializers.CharField(
            required=True,
        )
        procures = ProcureItemModelSerializer.StockWithQuantityAndRate(
            many=True,
        )

        class Meta(ProcureGroupMeta):
            fields = (
                'alias',
                'procures',
            )
            read_only_fields = ProcureGroupMeta.read_only_fields + ()

    class ProcureInfoReport(ListSerializer):
        procures = ProcureModelSerializer.ProcureItemsOnly(
            many=True,
        )
        supplier = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=('id', 'alias', 'company_name', 'first_name', 'last_name', 'code')
        )
        contractor = PersonOrganizationLiteSerializer(
            read_only=True,
            allow_null=True,
            fields=("id", "alias", "company_name", "first_name", "last_name", "code")
        )
        invoices = serializers.ListField(
            read_only=True,
            allow_null=True,
        )
        total_credit_amount = serializers.DecimalField(
            max_digits=19, decimal_places=3, read_only=True,
        )
        total_paid_amount = serializers.DecimalField(
            max_digits=19, decimal_places=3, read_only=True,
        )
        total_open_credit_balance = serializers.DecimalField(
            max_digits=19, decimal_places=3, read_only=True,
        )

        class Meta(ProcureGroupMeta):
            fields = ProcureGroupMeta.fields + (
                "alias",
                "date",
                "procures",
                "status",
                "supplier",
                "contractor",
                "invoices",
                "requisition",
                "total_amount",
                "total_discount",
                "credit_amount",
                "paid_amount",
                "credit_payment_term",
                "credit_payment_term_date",
                "credit_cost_percentage",
                "credit_cost_amount",
                "open_credit_balance",
                "cash_commission",
                "total_paid_amount",
                "total_credit_amount",
                "total_open_credit_balance",
                "credit_status"

            )
            read_only_fields = ProcureGroupMeta.read_only_fields + ()
