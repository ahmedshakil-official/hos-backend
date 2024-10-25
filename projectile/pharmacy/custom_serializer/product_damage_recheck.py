import logging

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer

from ecommerce.models import DeliverySheetItem,DeliverySheetInvoiceGroup

from pharmacy.enums import DamageProductType, RecheckProductType
from pharmacy.models import DamageProduct, Stock, Damage, Recheck, RecheckProduct

logger = logging.getLogger(__name__)

DECIMAL_ZERO = Decimal("0.000")

class DamageItemSerializer(ModelSerializer):
    class Meta:
        model = DamageProduct
        fields = [
            "stock",
            "quantity",
            "price",
            "remark",
            "type",
        ]

class DamageItemListSerializer(ModelSerializer):
    class Meta:
        model = DamageProduct
        fields = [
            "stock",
            "product_name",
            "product_image",
            "manufacturer_company_name",
            "quantity",
            "total_amount",
            "remark",
            "invoice_group",
            "type",
        ]
        read_only_fields = ["__all__"]




class RecheckItemSerializer(ModelSerializer):
    class Meta:
        model = RecheckProduct
        fields = ListSerializer.Meta.fields + (
            "stock",
            "quantity",
            "remark",
            "price",
            "order_quantity",
            "invoice_group",
            "total_amount",
            "is_approved",
            "type",
        )


class RecheckItemListSerializer(ModelSerializer):
    class Meta(RecheckItemSerializer):
        model = RecheckProduct
        fields = RecheckItemSerializer.Meta.fields + (
            "manufacturer_company_name",
            "product_name",
            "product_image",
            "approved_by",
            "approved_at",
        )
        read_only_fields = fields


class DamageItemsSerializer(ModelSerializer):
    class Meta:
        model = DamageProduct
        fields = DamageItemListSerializer.Meta.fields + [
            "damage",
            "discounted_price",
            "invoice_group",
        ]
        read_only_fields = fields


class DamageProductListSerializer(serializers.ModelSerializer):
    damage_items = serializers.ListField(
        child=DamageItemSerializer(), allow_empty=False, write_only=True
    )
    damage_products = DamageItemListSerializer(
        source="damage_io", many=True, read_only=True
    )

    class Meta:
        model = Damage
        fields = ListSerializer.Meta.fields + (
            "total_quantity",
            "total_amount",
            "reported_by",
            "reported_date",
            "remark",
            "invoice_group",
            "damage_items",
            "damage_products",
        )

        read_only_fields = ["damage_products", "reported_by"]

    def create(self, validated_data):
        request = self.context["request"]
        reported_by = request.user.get_person_organization_for_employee()
        damage_items = validated_data.pop("damage_items")
        invoice_group = validated_data.get("invoice_group", None)

        try:
            with transaction.atomic():
                damage_obj = Damage.objects.create(
                    reported_by_id=reported_by.id, **validated_data
                )
                damage_item_list = []
                total_amount = DECIMAL_ZERO
                total_quantity = DECIMAL_ZERO

                for item in damage_items:
                    stock_ = item.get("stock")
                    stock = Stock.objects.only("id").get(id=stock_.id)
                    type_ = item.get("type", None)
                    quantity = item.get("quantity")
                    price = Decimal(stock.product.trading_price)

                    total_amount = Decimal(price) * Decimal(quantity)
                    remark = item.get("remark")

                    manufacturing_company_name = (
                        stock.product.manufacturing_company.name
                    )

                    if type_ == DamageProductType.RETURN_DAMAGE:
                        if invoice_group is None:
                            raise ValidationError(
                                {"detail": "Please provide invoice id."}
                            )

                    damage_product = DamageProduct(
                        damage=damage_obj,
                        stock=stock,
                        manufacturer_company_name=manufacturing_company_name,
                        product_name=stock.product.name,
                        product_image=stock.product.image,
                        type=type_,
                        quantity=quantity,
                        price=price,
                        total_amount=total_amount,
                        remark=remark,
                    )

                    damage_item_list.append(damage_product)
                    total_amount += damage_product.price
                    total_quantity += damage_product.quantity

                damage_products = DamageProduct.objects.bulk_create(damage_item_list)

                if damage_products:
                    for item in damage_products:
                        stock = item.stock
                        stock.orderable_stock -= item.quantity
                        stock.save()

                damage_obj.total_amount = total_amount
                damage_obj.total_quantity = total_quantity
                damage_obj.save()

                return damage_obj

        except Exception as e:
            raise ValidationError({"Error", str(e)})


class DamageProductDetailSerializer(serializers.ModelSerializer):
    damage_items = serializers.ListField(
        child=DamageItemSerializer(), allow_empty=False, write_only=True
    )
    damage_products = DamageItemListSerializer(
        source="damage_io", many=True, read_only=True
    )

    class Meta:
        model = Damage
        fields = ListSerializer.Meta.fields + (
            "total_quantity",
            "total_amount",
            "reported_by",
            "reported_date",
            "remark",
            "invoice_group",
            "damage_items",
            "damage_products",
        )

        read_only_fields = ["damage_products", "reported_by"]

    def update(self, instance, validated_data):
        """
        Edge Case For Updating Damaged Product
        1. If type is RETURN_DAMAGE then we must provide invoice id
        """

        damage_items = validated_data.pop("damage_items", None)
        invoice_group = validated_data.get("invoice_group", None)

        if damage_items:
            for item in damage_items:
                stock_ = item.get("stock")

                try:
                    stock = Stock.objects.only("id").get(id=stock_.id)
                except Stock.DoesNotExist:
                    raise ValidationError({"detail": "Stock not found."})

                type_ = item.get("type", None)
                quantity = item.get("quantity")
                price = Decimal(stock.product.trading_price)
                total_amount = Decimal(price) * Decimal(quantity)
                remark = item.get("remark")


                # Check if the stock value is changing
                if not instance.damage_io.filter(stock_id=stock_.id).first():
                    raise ValidationError({"detail": "Stock value cannot be changed."})

                if type_ == DamageProductType.RETURN_DAMAGE:
                    if not invoice_group:
                        raise ValidationError({"detail": "Please provide invoice id."})

                item_to_update = DamageProduct.objects.filter(stock_id=stock_.id).first()
                previous_quantity = item_to_update.quantity

                item_to_update.type = type_
                item_to_update.invoice_group = invoice_group
                item_to_update.quantity = quantity
                item_to_update.price = price
                item_to_update.total_amount = total_amount
                item_to_update.remark = remark
                item_to_update.save()

                new_quantity = item_to_update.quantity

                qty = 0
                if previous_quantity < new_quantity:
                    qty = new_quantity - previous_quantity
                    stock.orderable_stock -= qty
                    stock.save()

                if previous_quantity > quantity:
                    qty = previous_quantity - quantity
                    stock.orderable_stock += qty
                    stock.save()

        return super().update(instance, validated_data)


class RecheckProductListSerializer(serializers.ModelSerializer):
    recheck_items = serializers.ListField(
        child=RecheckItemSerializer(), allow_empty=False, write_only=True
    )
    recheck_products = RecheckItemListSerializer(source="recheck_io", many=True, read_only=True)
    class Meta:
        model = Recheck
        fields = ListSerializer.Meta.fields + (
            "top_sheet",
            "rechecked_by",
            "rechecked_date",
            "total_missing_quantity",
            "total_extra_quantity",
            "recheck_amount",
            "recheck_items",
            "recheck_products"
        )
        read_only_fields = ["top_sheet", "rechecked_by", "rechecked_date", "recheck_products"]

    def create(self, validated_data):
        request = self.context["request"]
        rechecked_by = validated_data.pop("rechecked_by", None)
        if rechecked_by is None:
            rechecked_by = request.user.get_person_organization_for_employee()
        recheck_items = validated_data.pop("recheck_items")
        try:
            invoice_group = recheck_items[0].get("invoice_group")
        except:
            raise ValidationError({"detail":"Invoice is required."})

        delivery_sheet_items_ids = DeliverySheetInvoiceGroup.objects.only("id").filter(
            invoice_group__id=invoice_group.id
        ).values_list("delivery_sheet_item__id", flat=True)

        top_sheet = DeliverySheetItem.objects.only("id").filter(
            invoice_group_delivery_sheet__id__in=delivery_sheet_items_ids
        ).values_list("invoice_group_delivery_sheet_id", flat=True).first()

        try:
            with transaction.atomic():
                recheck_obj = Recheck.objects.create(top_sheet_id= top_sheet, rechecked_by=rechecked_by, **validated_data)
                recheck_item_list = []
                total_recheck_amount = DECIMAL_ZERO
                total_missing_quantity = DECIMAL_ZERO
                total_extra_quantity = DECIMAL_ZERO
                approved_by = None
                approved_at = None

                if recheck_items:
                    for item in recheck_items:
                        stock_ = item.get("stock")
                        stock = Stock.objects.only("id").get(id=stock_.id)

                        quantity = item.get("quantity")
                        remark = item.get("remark", "")
                        order_quantity = item.get("order_quantity")
                        price =Decimal(stock.product.trading_price) # total amount = discount amount
                        total_amount = Decimal(price) * Decimal(quantity)

                        is_approved = item.get("is_approved", False)
                        if is_approved:
                            approved_by = request.user.get_person_organization_for_employee()
                            approved_at = timezone.now()

                        type_ = item.get("type", None)

                        manufacturing_company_name = (
                            stock.product.manufacturing_company.name
                        )
                        product_name = stock.product.name
                        product_image = stock.product.image

                        recheck_item = RecheckProduct(
                            recheck = recheck_obj,
                            stock=stock,
                            quantity = quantity,
                            remark = remark,
                            price = price,
                            order_quantity=order_quantity,
                            total_amount = total_amount,
                            is_approved = is_approved,
                            type = type_,
                            product_name =product_name,
                            product_image = product_image,
                            manufacturer_company_name= manufacturing_company_name,
                            invoice_group = invoice_group,
                            approved_by = approved_by,
                            approved_at = approved_at
                        )

                        recheck_item_list.append(recheck_item)
                        total_recheck_amount += total_amount

                    recheck_products = RecheckProduct.objects.bulk_create(recheck_item_list)

                    if recheck_products:
                        for item in recheck_products:
                            stock = item.stock

                            if item.type == RecheckProductType.EXTRA and is_approved:
                                stock.orderable_stock += item.quantity
                                stock.save()
                                total_extra_quantity += item.quantity

                            if item.type == RecheckProductType.MISSING and is_approved:
                                if stock.orderable_stock < 0:
                                    raise ValidationError("Orderable stock is less than 0.")
                                stock.orderable_stock -= item.quantity
                                stock.save()
                                total_missing_quantity += item.quantity

                    recheck_obj.recheck_amount = total_recheck_amount
                    recheck_obj.total_extra_quantity = total_extra_quantity
                    recheck_obj.total_missing_quantity =  total_missing_quantity
                    recheck_obj.save()

                return recheck_obj

        except Exception as e:
            raise ValidationError({"detail": str(e)})


class RecheckProductDetailSerializer(serializers.ModelSerializer):
    recheck_items = serializers.ListField(
        child=RecheckItemSerializer(), allow_empty=False, write_only=True
    )
    recheck_products = RecheckItemListSerializer(source="recheck_io", many=True, read_only=True)
    class Meta:
        model = Recheck
        fields = ListSerializer.Meta.fields + RecheckProductListSerializer.Meta.fields

    def update(self, instance, validated_data):
        recheck_items = validated_data.pop("recheck_items")
        request = self.context["request"]
        approved_by = request.user.get_person_organization_for_employee()

        if recheck_items:

            for item in recheck_items:
                stock_ = item.get("stock")
                try:
                    stock = Stock.objects.only("id").get(id=stock_.id)
                except Stock.DoesNotExist:
                    raise ValidationError({"detail": "Stock not found."})

                # Check if the stock value is changing
                if not instance.recheck_io.filter(stock_id=stock_.id).first():
                    raise ValidationError({"detail": "Stock value cannot be changed."})

                is_approved = item.get("is_approved", False)
                type_ = item.get("type", None)
                quantity = item.get("quantity")
                price = Decimal(stock.product.trading_price)

                total_amount = Decimal(price) * Decimal(quantity)

                item_to_update = RecheckProduct.objects.filter(stock_id=stock_.id).first()
                item_to_update.quantity = quantity
                item_to_update.price = price
                item_to_update.total_amount = Decimal(total_amount)
                if is_approved:
                    item_to_update.is_approved = is_approved
                    item_to_update.approved_by = approved_by
                    item_to_update.approved_at = timezone.now()
                item_to_update.save()

        return super().update(instance, validated_data)


class RecheckProductsSerializer(ModelSerializer):

    class Meta:
        model = RecheckProduct
        fields = RecheckItemListSerializer.Meta.fields + (
            "recheck",
        )
        read_only_fields = fields
