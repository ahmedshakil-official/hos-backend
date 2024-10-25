from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView

from core.permissions import (
    CheckAnyPermission,
    IsSuperUser,
    StaffIsAdmin,
    StaffIsProcurementManager,
    StaffIsTelemarketer,
)

from deep_link.models import DeepLink

from deep_link.serializers.deep_links import DeepLinkModelSerializer


class DeepLinkList(ListCreateAPIView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsTelemarketer,
    )
    permission_classes = (CheckAnyPermission, )
    queryset = DeepLink().get_all_actives()
    serializer_class = DeepLinkModelSerializer.List

    def get_serializer_class(self):
        if self.request.method == "GET":
            return DeepLinkModelSerializer.List
        return DeepLinkModelSerializer.Post
