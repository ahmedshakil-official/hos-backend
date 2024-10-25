from core.permissions import (
    CheckAnyPermission,
    StaffIsAdmin,
)
from ..models import OrderTracking
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import datetime
from rest_framework.generics import ListAPIView


class InvoiceStatusChangeLog(APIView):
    available_permission_classes = StaffIsAdmin
    permission_classes = (CheckAnyPermission,)

    def get(self, request):

        current_date = datetime.date.today()
        query_params_date = self.request.query_params.get(
            "date", str(current_date))

        try:
            date_format = "%Y-%m-%d"
            date_object = datetime.datetime.strptime(
                query_params_date, date_format)
            order_tracking_objects = (
                OrderTracking.objects.filter(
                    date__year=date_object.year,
                    date__month=date_object.month,
                    date__day=date_object.day,
                )
                .select_related("order")
                .order_by("order__tentative_delivery_date")
                .distinct("order__tentative_delivery_date")
            )
            final_response = []
            for single_order_tracking_object in order_tracking_objects:
                same_tentative_delivery_date_order_tracking_obj = OrderTracking.objects.filter(
                    order__tentative_delivery_date=single_order_tracking_object.order.tentative_delivery_date
                ).select_related(
                    "order"
                ).distinct("order__id")
                final_response.append({
                    str(single_order_tracking_object.order.tentative_delivery_date): [
                        single_order_tracking_obj.order.id
                        for single_order_tracking_obj in same_tentative_delivery_date_order_tracking_obj
                    ],
                })

            return Response(list(final_response), status=status.HTTP_200_OK)
        except:
            return Response(
                {
                    "error": "Not Found",
                    "message": f"No data found. Check your date time format. Date time format should be __url__?date={current_date}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
