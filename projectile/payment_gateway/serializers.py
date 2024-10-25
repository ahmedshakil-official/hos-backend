# from rest_framework import serializers
# from rest_framework.serializers import (
#     ModelSerializer,
# )
# from core.custom_serializer.organization import (
#     OrganizationModelSerializer,
# )
# from .models import PaymentRequest, PaymentIpn, PaymentResponse


# class PaymentRequestSerializer(ModelSerializer):
#     organization = OrganizationModelSerializer.Lite()
#     # pylint: disable=old-style-class, no-init
#     class Meta:
#         model = PaymentRequest
#         fields = (
#             'date',
#             'organization',
#             'payment_purpose',
#             'payment_month',
#         )


# class PaymentResponseSerializer(ModelSerializer):
#     data = serializers.SerializerMethodField()
#     # pylint: disable=old-style-class, no-init
#     class Meta:
#         model = PaymentResponse
#         fields = (
#             'data',
#         )

#     def get_data(self, _obj):
#         return {
#             'status': _obj.data.get('status', None),
#             'discount_remarks': _obj.data.get('discount_remarks', None),
#         }


# class PaymentIPNSerializer(ModelSerializer):
#     payment_request = PaymentRequestSerializer()
#     data = serializers.SerializerMethodField()
#     response = PaymentResponseSerializer(many=True)
#     # pylint: disable=old-style-class, no-init
#     class Meta:
#         model = PaymentIpn
#         fields = (
#             'payment_request',
#             'data',
#             'response'
#         )

#     def get_data(self, _obj):
#         return {
#             'amount': float(_obj.data.get('amount', 0)),
#             'card_issuer': _obj.data.get('card_issuer', None),
#             'risk_title': _obj.data.get('risk_title', None),
#             'error': _obj.data.get('error', None),
#             'status': _obj.data.get('status', None),
#         }
