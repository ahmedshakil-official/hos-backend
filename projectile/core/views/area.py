"""Views for area related model."""
from rest_framework import status
from rest_framework.response import Response

from core.views.common_view import (
    ListCreateAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
    CreateAPICustomView,
)

from core.permissions import (
    CheckAnyPermission,
    IsSuperUser,
    StaffIsAdmin,
    StaffIsTelemarketer,
)

from core.models import Area

from core.custom_serializer.area import AreaModelSerializer


class AreaList(ListCreateAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsTelemarketer,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = AreaModelSerializer.List

    def get_queryset(self, related_fields=None, only_fields=None):
        return Area().get_all_actives()


class AreaDetail(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsTelemarketer,
    )
    permission_classes = (CheckAnyPermission,)
    queryset = Area().get_all_actives()
    lookup_field = "alias"
    serializer_class = AreaModelSerializer.Detail


class AreaBulkUpdate(CreateAPICustomView):
    """View for updating discount factor by area"""

    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)

    serializer_class = AreaModelSerializer.BulkUpdateSerializer

    def post(self, request, *args, **kwargs):
        try:
            request_data = request.data
            serializer = self.serializer_class(data=request_data, many=True)
            if serializer.is_valid(raise_exception=True):
                for data in serializer.validated_data:
                    """Getting area by alias"""
                    area_alias = data.get("alias", None)
                    area = Area.objects.get(alias=area_alias)
                    """Create a list of update fields for bulk update"""
                    update_fields = []
                    """Getting discount factor"""
                    discount_factor = data.get("discount_factor")
                    """Updating discount factor if it is not None"""
                    if discount_factor is not None:
                        area.discount_factor = discount_factor
                        """Added discount factor in update fields list"""
                        update_fields.append("discount_factor")

                    """Save the area in update fields list if any fields were updated"""
                    if update_fields:
                        area.save(update_fields=update_fields)

            response = {
                "message": "Success"
            }
            return Response(response, status=status.HTTP_200_OK)

        except Exception as exception:
            content = {"error": "{}".format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
