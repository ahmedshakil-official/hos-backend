from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.views.common_view import (
    CreateAPICustomView,
)


from core.permissions import (
    CheckAnyPermission,
    IsSuperUser,
    StaffIsAdmin,
)
from ecommerce.serializers.invoice_group_delivery_sheet import InvoiceGroupDeliverySheetModelSerializer


from ..serializers.invoice_group_deliver_sub_sheet import (
    SubSheetPostSerializer,
)


class InvoiceGroupDeliverySubSheetCreate(APIView):
    available_permission_classes = (StaffIsAdmin,)
    permission_classes = (CheckAnyPermission,)
    serializer_class = SubSheetPostSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            data = serializer.save()
            serialized_data = InvoiceGroupDeliverySheetModelSerializer.List(data).data
            return Response(
                serialized_data, status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )
