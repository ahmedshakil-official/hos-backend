from django.db.models import Sum, Case, When, F, IntegerField, Count
from django.db.models.functions import Coalesce
from rest_framework import serializers
from rest_framework.serializers import Serializer

from common.utils import get_item_from_list_of_dict
from common.enums import Status
from core.utils import construct_organization_object_from_dictionary

from ecommerce.models import OrderInvoiceGroup, ShortReturnItem
from ecommerce.enums import ShortReturnLogType

class ResponsibleEmployeeWiseInvoiceGroupDeliverySheetSerializer(Serializer):
    order_invoice_group_ids = serializers.ListField()
    order_by_organization = serializers.SerializerMethodField()
    unique_item = serializers.IntegerField()
    total_item = serializers.IntegerField()
    short_return_quantity = serializers.SerializerMethodField()
    order_invoice_group_count = serializers.IntegerField()
    order_invoice_group_amounts = serializers.SerializerMethodField()

    def get_order_by_organization(self, _obj):
        return {
            'id': _obj.get('order_by_organization', None),
            'alias': _obj.get('order_by_organization__alias', None),
            'name': _obj.get('order_by_organization__name', ''),
            'primary_mobile': _obj.get('order_by_organization__primary_mobile', ''),
            'address': _obj.get('order_by_organization__address', ''),
        }

    def calculate_grand_total(self, data):
        return float("{:.3f}".format(data.get('sub_total', 0) \
            - data.get('discount', 0) \
            + data.get('round_discount', 0) \
            + data.get('additional_cost', 0) \
            - data.get('additional_discount', 0)))

    def get_short_return_amount(self, group_id):
        return OrderInvoiceGroup.objects.only('id').get(
            pk=group_id
        ).get_total_short_return_data()

    def get_order_invoice_group_amounts(self, _obj):
        from operator import itemgetter
        data = _obj.get('order_invoice_group_amounts', [])
        data = sorted([dict(t) for t in {tuple(d.items()) for d in data}], key=itemgetter('id'))
        data_list = []
        for item in data:
            existing_item = get_item_from_list_of_dict(data_list, 'id', item['id'])
            if existing_item:
                existing_item['orders'].append(item['orders'])
            else:
                item['orders'] = [item['orders']]
                data_list.append(item)
        results = [{**item, 'grand_total': self.calculate_grand_total(item), **self.get_short_return_amount(item.get('id'))} for item in data_list]
        return results

    def get_short_return_quantity(self, _obj):
        data = _obj.get('order_invoice_group_amounts', [])
        group_id_list = list(set(map(lambda item: item.get('id'), data)))
        short_return_items = ShortReturnItem.objects.filter(
            short_return_log__order__invoice_group__pk__in=group_id_list
        ).only(
            'stock_id',
            'quantity',
        ).aggregate(
            unique_short_quantity=Count(Case(When(
                status=Status.ACTIVE,
                type=ShortReturnLogType.SHORT,
                then=F('stock_id')),
                output_field=IntegerField()), distinct=True),
            unique_return_quantity=Count(Case(When(
                status=Status.ACTIVE,
                type=ShortReturnLogType.RETURN,
                then=F('stock_id')),
                output_field=IntegerField()), distinct=True),
            total_short_quantity=Coalesce(Sum(Case(When(
                status=Status.ACTIVE,
                type=ShortReturnLogType.SHORT,
                then=F('quantity')),
                output_field=IntegerField())), 0),
            total_return_quantity=Coalesce(Sum(Case(When(
                status=Status.ACTIVE,
                type=ShortReturnLogType.RETURN,
                then=F('quantity')),
                output_field=IntegerField())), 0),
        )
        return short_return_items


class DeliverySheetShortReturnListProductWiseSerializer(Serializer):
    """
    Serializer for DeliverySheetShortReturnListProductWise
    """
    stock_id = serializers.IntegerField()
    stock_alias = serializers.UUIDField(source='stock__alias')
    product_name = serializers.CharField(source='stock__product__name')
    product_form = serializers.CharField(source='stock__product__form__name')
    product_strength = serializers.CharField(source='stock__product__strength')
    total_order_quantity = serializers.FloatField()
    total_short_quantity = serializers.FloatField()
    total_return_quantity = serializers.FloatField()


class DeliverySheetStockShortReturnListInvoiceGroupWiseSerializer(Serializer):
    """
    Serializer for DeliverySheetStockShortReturnListInvoiceGroupWise
    """
    invoice_group = serializers.IntegerField(source='purchase__invoice_group_id')
    total_order_quantity = serializers.FloatField()
    total_short_quantity = serializers.FloatField()
    total_return_quantity = serializers.FloatField()
