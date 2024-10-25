from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.response import Response

from common.enums import Status
from common.helpers import get_date_from_period
from core.permissions import StaffIsAdmin, CheckAnyPermission
from core.views.common_view import ListAPICustomView, CreateAPICustomView, ListCreateAPICustomView
from pharmacy.enums import OrderTrackingStatus
from ..models import OrderInvoiceGroup
from ..serializers.order_invoice_group import OrderInvoiceGroupModelSerializer


class OrderRatingListCreate(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)

    serializer_class = OrderInvoiceGroupModelSerializer.OrderRatingPost
    pagination_class = None

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return OrderInvoiceGroupModelSerializer.OrderRatingList
        return OrderInvoiceGroupModelSerializer.OrderRatingPost

    def get_queryset(self, related_fields=None, only_fields=None):
        return OrderInvoiceGroup.objects.filter(
            status=Status.ACTIVE,
            order_by_organization_id=self.request.user.organization_id,
            delivery_date__gte=get_date_from_period("1w"),
            current_order_status__in=[
                OrderTrackingStatus.PORTER_DELIVERED,
                OrderTrackingStatus.PORTER_PARTIAL_DELIVERED,
            ],
            customer_rating=0,
        ).order_by('-delivery_date', '-updated_at')

    def post(self, request, *args, **kwargs):
        try:
            request_data = request.data
            serializer = self.serializer_class(data=request_data, many=True)
            if serializer.is_valid(raise_exception=True):
                obj_to_be_updated = []
                for data in serializer.validated_data:
                    invoice_group = data.get('alias', None)
                    customer_rating = data.get('customer_rating', None)
                    customer_comment = data.get('customer_comment', None)
                    obj_to_be_updated.append(
                        OrderInvoiceGroup(
                            id=invoice_group.id,
                            customer_rating=customer_rating,
                            customer_comment=customer_comment,
                        )
                    )
                OrderInvoiceGroup.objects.bulk_update(
                    obj_to_be_updated,
                    fields=[
                        'customer_rating',
                        'customer_comment',
                    ]
                )
            response = {
                "message": "Success"
            }
            return Response(response, status=status.HTTP_200_OK)
        except Exception as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
