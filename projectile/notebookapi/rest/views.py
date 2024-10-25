
from rest_framework.views import APIView
from rest_framework.response import Response

from ..notebooks.pharmacies import get_dropped_pharmacies


class DroppedPharmacyList(APIView):
    def get(self, request):
        days_ago = request.GET.get('days_ago', None)
        drop_days = request.GET.get('drop_days', None)
        data = get_dropped_pharmacies(days_ago=days_ago, drop_days=drop_days)
        return Response(data)
