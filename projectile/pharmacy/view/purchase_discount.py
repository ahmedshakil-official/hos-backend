from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from pharmacy.utils import get_discount_rules


class GetDiscountRules(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        data = get_discount_rules()
        return Response(
            data,
            status=status.HTTP_200_OK
        )
