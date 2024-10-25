# import json
# from django.db import transaction
# from django.db.models import Prefetch
# from rest_framework.views import APIView
# from rest_framework import status, generics
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny, IsAuthenticated

# from common.helpers import _create_object
# from common.enums import Status

# from core.models import PersonOrganization
# from core.permissions import CheckAnyPermission
# from .utils import initialize_payment, validate_order, get_instance_by_filter
# from .models import PaymentRequest, PaymentIpn, PaymentResponse
# from .serializers import PaymentIPNSerializer


# class CreatePayment(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         if not isinstance(request.data.get('order', {}), dict):
#             initialization_reqest_data = json.loads(request.data.get('order', {}))
#         else:
#             initialization_reqest_data = request.data
#         try:
#             response = initialize_payment(self, initialization_reqest_data)
#             response_data = {
#                 "data": response['GatewayPageURL'],
#                 "logo": response['storeLogo'],
#                 "status": response['status'].lower()
#             }
#             return Response(response_data, status=status.HTTP_200_OK)

#         except Exception as exception:
#             content = {'error': '{}'.format(exception)}
#             return Response(content, status=status.HTTP_400_BAD_REQUEST)


# class ValidateIpnOrder(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         try:
#             ipn_data = request.data
#             # Store IPN data to db
#             _create_object(
#                 PaymentIpn,
#                 {
#                     "data": ipn_data,
#                     "payment_request": get_instance_by_filter(
#                         PaymentRequest,
#                         {
#                             "data__tran_id": ipn_data.get('tran_id', "")
#                         }
#                     )
#                 }
#             )
#             response = validate_order(ipn_data)
#             _create_object(
#                 PaymentResponse,
#                 {
#                     "data": response,
#                     "ipn": get_instance_by_filter(
#                         PaymentIpn,
#                         {
#                             "data__val_id": ipn_data.get('val_id', "")
#                         }
#                     )
#                 }
#             )
#             response_data = {
#                 "ipn_status": ipn_data.get('status'),
#                 "validation_status": response['status']
#             }
#             return Response(response_data, status=status.HTTP_200_OK)

#         except Exception as exception:
#             content = {'error': '{}'.format(exception)}
#             return Response(content, status=status.HTTP_400_BAD_REQUEST)


# class PaymentList(generics.ListAPIView):
#     available_permission_classes = (
#         IsAuthenticated,
#     )
#     permission_classes = (CheckAnyPermission, )

#     serializer_class = PaymentIPNSerializer
#     pagination_class = None

#     def get_queryset(self):
#         responses = PaymentResponse.objects.filter(status=Status.ACTIVE)
#         belongs_to = PersonOrganization.objects.filter(
#             person=self.request.user,
#             status=Status.ACTIVE,
#         ).values('organization')

#         return PaymentIpn.objects.filter(
#             status=Status.ACTIVE,
#             payment_request__organization__in=belongs_to
#         ).select_related(
#             'payment_request',
#         ).prefetch_related(
#             Prefetch(
#                 'paymentresponse_set',
#                 queryset=responses,
#                 to_attr='response'
#             )
#         )

