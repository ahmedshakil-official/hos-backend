from django.db import transaction
from rest_framework import serializers
from django.utils.translation import gettext as _
from common.choices import WriteChoices
from common.custom_serializer.cu_base_organization_wise_serializer import (
    ListSerializer,
)
from common.custom_serializer_field import ForeignKeyAliasField
from common.enums import Status
from pharmacy.custom_serializer.stock import DistributorSalesableStock
from pharmacy.models import StockReminder


# pylint: disable=old-style-class, no-init
class ProductRestockReminderMeta(ListSerializer.Meta):
    model = StockReminder

    fields = ListSerializer.Meta.fields + (
        'stock',
        'preferable_price',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (

    )


class ProductRestockReminderModelSerializer:
    class List(ListSerializer):
        stock = DistributorSalesableStock.ListForGeneralUser()

        class Meta(ProductRestockReminderMeta):
            fields = ProductRestockReminderMeta.fields + (
            )
            read_only_fields = ProductRestockReminderMeta.read_only_fields + (

            )

    class ListForAdmin(ListSerializer):
        stock = DistributorSalesableStock.ListForSuperAdmin()

        class Meta(ProductRestockReminderMeta):
            fields = ProductRestockReminderMeta.fields + (
                'reminder_count',
            )
            read_only_fields = ProductRestockReminderMeta.read_only_fields + (

            )

    class Lite(ListSerializer):
        stock = ForeignKeyAliasField()

        class Meta(ProductRestockReminderMeta):
            fields = (
                'stock',
                'preferable_price',
            )

    class Post(ListSerializer):
        type = serializers.ChoiceField(choices=WriteChoices, write_only=True)

        class Meta(ProductRestockReminderMeta):
            fields = ProductRestockReminderMeta.fields + (
                'type',
            )
            read_only_fields = ProductRestockReminderMeta.read_only_fields + (

            )

        def validate_stock(self, value):
            choice = self.context['request'].data.get('type')
            if choice == WriteChoices.POST:
                stock = self.Meta.model.objects.filter(
                    organization_id=self.context['request'].user.organization_id,
                    stock=value,
                    status=Status.ACTIVE,
                    reminder_count=0,
                )
                if stock.exists():
                    raise serializers.ValidationError(
                        "You have already set a reminder for this product."
                    )
            return value

        @transaction.atomic
        def create(self, validated_data):
            try:
                choice = validated_data.pop('type')
                if choice == WriteChoices.POST:
                    validated_data['organization_id'] = self.context['request'].user.organization_id
                    validated_data['status'] = Status.ACTIVE
                    validated_data['reminder_count'] = 0
                    return self.Meta.model.objects.create(**validated_data)
                elif choice == WriteChoices.DELETE:
                    instance = self.Meta.model.objects.select_for_update().get(
                        organization_id=self.context['request'].user.organization_id,
                        stock_id=validated_data['stock'].id,
                        status=Status.ACTIVE,
                    )
                    instance.status = Status.INACTIVE
                    instance.save(update_fields=['status'])
                    return instance

            except Exception as ObjectDoesNotExist:
                error = {
                    'detail': _('OBJECT_DOES_NOT_EXIST')
                }
                raise serializers.ValidationError(error)

    class Update(ListSerializer):
        class Meta(ProductRestockReminderMeta):
            fields = (
                'preferable_price',
            )
            read_only_fields = ProductRestockReminderMeta.read_only_fields + (

            )
