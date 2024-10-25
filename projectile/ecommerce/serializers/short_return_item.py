import decimal
from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework import serializers

from common.exception_handler import ValidationError
from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from core.custom_serializer.person_organization import PersonOrganizationModelSerializer

from core.serializers import PersonOrganizationEmployeeSearchSerializer
from core.custom_serializer.organization import OrganizationModelSerializer
from pharmacy.custom_serializer.purchase import DistributorOrderForShortReturnLogSerializer
from pharmacy.models import StockIOLog

from ..models import ShortReturnItem, ShortReturnLog
from common.enums import Status


class ShortReturnLogLiteSerializer(serializers.ModelSerializer):
    received_by = PersonOrganizationEmployeeSearchSerializer()
    approved_by = PersonOrganizationModelSerializer.MinimalList()
    order = DistributorOrderForShortReturnLogSerializer()
    order_by_organization = OrganizationModelSerializer.Lite()

    # pylint: disable=old-style-class, no-init
    class Meta:
        model = ShortReturnLog
        fields = (
            'id',
            'date',
            'received_by',
            'approved_by',
            'order_by_organization',
            'order',
            'invoice_group',
            'order_amount',
            'short_return_amount',
            'type',
            'round_discount',
            'remarks',
        )


class ShortReturnItemMeta(ListSerializer.Meta):
    model = ShortReturnItem
    fields = ListSerializer.Meta.fields + (
        'id',
        'alias',
        'product_name',
        'type',
        'quantity',
        'rate',
        'date',
        'discount_rate',
        'discount_total',
        'vat_rate',
        'vat_total',
        'tax_total',
        'tax_rate',
        'stock',
        'stock_io',
        'order_quantity',
        'unit_name',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class ShortReturnItemModelSerializer:
    class Post(ListSerializer):
        class Meta(ShortReturnItemMeta):
            fields = ShortReturnItemMeta.fields + (

            )
            read_only_fields = ShortReturnItemMeta.read_only_fields + ()

        def validate(self, values):
            invoice_group_id = self.context.get("request").data[0]["invoice_group"]
            order_ids = [item["order"] for item in self.context.get("request").data]
            quantity = values.get("quantity", 0)
            stock_id = values["stock"].id
            product_name = values.get("product_name", "")
            short_return_quantity = ShortReturnItem.objects.filter(
                status__in=[Status.ACTIVE, Status.DRAFT],
                stock_id=stock_id,
                short_return_log__order__id__in=order_ids,
                short_return_log__invoice_group__id=invoice_group_id,
            ).aggregate(qty_total=Coalesce(Sum('quantity'), decimal.Decimal(0))).get(
                "qty_total", 0)
            order_quantity = StockIOLog.objects.filter(
                status=Status.DISTRIBUTOR_ORDER,
                stock_id=stock_id,
                purchase__id__in=order_ids,
            ).aggregate(qty_total=Coalesce(Sum('quantity'), 0.00)).get(
                "qty_total", 0)
            if (short_return_quantity + quantity) > order_quantity:
                error = {
                    "stock_id": stock_id,
                    "product_name": product_name,
                    "message": "Short Return Quantity can't be greater than order quantity"
                }
                raise ValidationError(error)
            return values

    class List(ListSerializer):
        short_return_log =ShortReturnLogLiteSerializer()

        class Meta(ShortReturnItemMeta):
            fields = ShortReturnItemMeta.fields + (
                'status',
                'short_return_log',
            )
            read_only_fields = ShortReturnItemMeta.read_only_fields + ()

    class Details(ListSerializer):
        class Meta(ShortReturnItemMeta):
            fields = ShortReturnItemMeta.fields + (
            )
            read_only_fields = ShortReturnItemMeta.read_only_fields + ()