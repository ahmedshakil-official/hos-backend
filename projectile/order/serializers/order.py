"""Serailizers for order related models."""

from rest_framework import serializers


class OrderLiteSerializerV2(serializers.Serializer):
    id = serializers.IntegerField()
    alias = serializers.UUIDField()
    grand_total = serializers.DecimalField(max_digits=19, decimal_places=2)
    tentative_delivery_date = serializers.DateTimeField(read_only=True)
    is_queueing_order = serializers.BooleanField()
