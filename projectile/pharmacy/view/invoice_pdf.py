import os
from datetime import datetime
from rest_framework.generics import (
    ListAPIView,
)
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from common.enums import Status

from core.permissions import (
    CheckAnyPermission,
    IsSuperUser,
    StaffIsAdmin,
    AnyLoggedInUser,
)
from core.views.common_view import ListAPICustomView
from ..invoice_helpers import create_pdf_invoice_lazy
from ..filters import DistributorOrderListFilter
from ..enums import DistributorOrderType, PurchaseType
from ..models import Purchase, InvoiceFileStorage
from ..custom_serializer.invoice_file_storage import InvoiceFileStorageModelSerializer

class GeneratePdfInvoice(ListAPIView):
    available_permission_classes = (StaffIsAdmin, )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        try:
            repeat = int(self.request.query_params.get('repeat', 3))
            user_id = request.user.id
            filters = {
                "status": Status.DISTRIBUTOR_ORDER,
                "distributor_order_type": DistributorOrderType.ORDER,
                "purchase_type": PurchaseType.VENDOR_ORDER,
                "distributor": self.request.user.organization_id
            }
            queryset = Purchase.objects.filter(**filters)
            non_empty_list = list(v for k, v in (request.GET.dict()).items() if v)
            if len(non_empty_list) < 2:
                content = {'error': 'You must apply filter for generating invoice'}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)
            orders = DistributorOrderListFilter(request.GET, queryset).qs
            orders_qs = orders.values_list('pk', flat=True)
            order_ids = list(orders_qs)
            order_count = orders_qs.count()

            if order_count > 1000:
                content = {'error': f"The filter have {order_count} orders, More than 1000 orders is not allowed to proceed at once."}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)

            now = datetime.now()
            dt_string = now.strftime("%d-%m-%Y-%H%M%S")
            domain = os.environ.get('DOMAIN', 'localhost:8000')
            chunk_size = 50
            data_length = len(order_ids)
            number_of_operations = int((data_length / chunk_size) + 1)
            lower_limit = 0
            itr_count = 0
            upper_limit = chunk_size
            for _ in range(0, number_of_operations):
                data_limit = order_ids[lower_limit : upper_limit]
                lower_limit = upper_limit
                upper_limit += chunk_size
                if data_limit:
                    itr_count = _ + 1
                    output_file = f"invoice-{itr_count}-{dt_string}.pdf"
                    create_pdf_invoice_lazy.delay(order_ids=data_limit, outfile_name=output_file, repeat=repeat, entry_by_id=user_id)

            response = {
                'status': 'Ok',
                'message': f"Invoice generated for {order_count} orders with repeat {repeat}, splitted in {itr_count} file."
            }
            return Response(response, status=status.HTTP_200_OK)

        except Exception as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class OrderPdfInvoiceList(ListAPICustomView):
    """List of all pdf invoice"""
    available_permission_classes = (
        StaffIsAdmin,
    )
    serializer_class = InvoiceFileStorageModelSerializer.List

    def get_queryset(self):
        is_super_user = self.request.user.is_superuser
        queryset =  InvoiceFileStorage.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id
        ).order_by('-pk')

        if is_super_user:
            return queryset
        else:
            return queryset.filter(entry_by=self.request.user.id)