from rest_framework import generics, parsers

from ..filters import ScriptFileListFilter
from ..permissions import (
    IsSuperUser,
    StaffIsAdmin,
    CheckAnyPermission,
    StaffIsMonitor, StaffIsProcurementManager,
)


from ..serializers import (
    ScriptFileStorageSerializer,
)
from common.enums import Status

from ..models import (
    ScriptFileStorage,
)
from ..enums import FilePurposes


class ScriptFileStorageGeneric(object):
    serializer_class = ScriptFileStorageSerializer
    permission_classes = (IsSuperUser,)

    def get_queryset(self):
        name = self.request.query_params.get('keyword', None)
        file_purposes = self.request.query_params.get(
            'file_purposes',
            f"{FilePurposes.SCRIPT}, {FilePurposes.DISTRIBUTOR_STOCK}, {FilePurposes.PURCHASE_PREDICTION}"
        )
        if file_purposes:
            file_purposes = file_purposes.split(",")
        files = ScriptFileStorage.objects.filter(
            status=Status.ACTIVE, file_purpose__in=file_purposes)
        if name:
            return files.filter(name__icontains=name)
        return files

    def perform_create(self, serializer):
        serializer.save(entry_by=self.request.user)


class ScriptFileStorageList(ScriptFileStorageGeneric, generics.ListCreateAPIView):

    available_permission_classes = (
        StaffIsMonitor,
        IsSuperUser,
        StaffIsAdmin,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission, )

    filterset_class = ScriptFileListFilter

    parser_classes = (parsers.FormParser, parsers.MultiPartParser, )


class ScriptFileStorageDetails(ScriptFileStorageGeneric, generics.RetrieveUpdateDestroyAPIView):
    lookup_field = 'alias'
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission, )
