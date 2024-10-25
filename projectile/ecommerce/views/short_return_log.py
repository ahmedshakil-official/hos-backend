from validator_collection import checkers
from rest_framework import status
from rest_framework.response import Response

from common.enums import Status
from core.views.common_view import(
    ListCreateAPICustomView,
    CreateAPICustomView,
    ListAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
)
from core.permissions import (
    CheckAnyPermission,
    IsSuperUser,
    StaffIsAdmin,
    AnyLoggedInUser,
    StaffIsDeliveryMan,
    StaffIsMarketer,
    StaffIsTelemarketer,
    StaffIsDeliveryHub,
    StaffIsFrontDeskProductReturn,
    StaffIsSalesManager,
    StaffIsSalesCoordinator,
    StaffIsDistributionT2,
    StaffIsDistributionT3,
)
from ecommerce.serializers.short_return_log import ShortReturnLogModelSerializer, ApproveShortReturnsSerializer
from ecommerce.serializers.short_return_item import ShortReturnItemModelSerializer
from ecommerce.models import ShortReturnItem, ShortReturnLog
from ..enums import ShortReturnLogType
from ..tasks import send_push_notification_on_short
from ..filters import ShortReturnItemFilter, ShortReturnLogListFilter, ShortReturnLogListWithoutTypeFilter


class ShortReturnLogListCreate(ListCreateAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsFrontDeskProductReturn,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsTelemarketer,
        StaffIsSalesManager,
    )
    permission_classes = (CheckAnyPermission, )
    filterset_class = ShortReturnLogListFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ShortReturnLogModelSerializer.List
        return ShortReturnLogModelSerializer.Post

    def get_queryset(self, related_fields=None, only_fields=None):
        return ShortReturnLog.objects.exclude(
            status=Status.INACTIVE
        ).select_related(
            'received_by',
            'order_by_organization',
            'approved_by',
        )

    def get_serializer(self, *args, **kwargs):
        """ if an array is passed, set serializer to many """
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    def post(self, request):
        _data = request.data
        invoice_group_ids = [item['invoice_group'] for item in _data if 'invoice_group' in item]
        # If request is from reporter server use code to find entry by user
        entry_by_id = self.request.META.get('HTTP_ENTRY_BY_ID', '')
        if entry_by_id and checkers.is_integer(entry_by_id):
            entry_by_id = int(entry_by_id)
        else:
            entry_by_id = self.request.user.id
        try:
            serializer = self.get_serializer(
                data=request.data,
                context={'request': request}
            )
            _many = serializer.many
            if serializer.is_valid(raise_exception=True):
                serializer = serializer.save(
                    organization_id=request.user.organization_id,
                    entry_by_id=entry_by_id
                )
                results = ShortReturnLogModelSerializer.List(serializer, many=_many)
                if invoice_group_ids:
                    send_push_notification_on_short.apply_async(
                        (invoice_group_ids[0],  request.user.id),
                        countdown=5,
                        retry=True, retry_policy={
                            'max_retries': 10,
                            'interval_start': 0,
                            'interval_step': 0.2,
                            'interval_max': 0.2,
                        }
                    )
                return Response(results.data[:], status=status.HTTP_201_CREATED)

        except Exception as exception:
            if hasattr(exception, 'detail'):
                if type(exception.detail) is dict or type(exception.detail) is list:
                    return Response(
                        {
                            "error": exception.args[0]
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            exception_str = exception.args[0] if exception.args else str(exception)
            content = {'error': '{}'.format(exception_str)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class ShortReturnLogListItemWise(ListAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsMarketer,
        StaffIsTelemarketer,
        StaffIsDeliveryHub,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsFrontDeskProductReturn,
        StaffIsSalesCoordinator,
        StaffIsSalesManager,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = ShortReturnItemModelSerializer.List
    filterset_class = ShortReturnItemFilter

    def get_queryset(self):
        status = self.request.query_params.get('status', None)
        if status is not None:
            filters = {
                "organization__id": self.request.user.organization_id
            }
        else:
            filters = {
                "status": Status.ACTIVE,
                "organization__id": self.request.user.organization_id
            }
        queryset = ShortReturnItem.objects.filter(
            **filters
        ).select_related(
            'short_return_log',
            'short_return_log__received_by',
            'short_return_log__approved_by',
            'short_return_log__order_by_organization',
            'short_return_log__order',
            'short_return_log__order__responsible_employee',
        )
        return queryset.order_by('-pk')


class ApproveShortReturns(CreateAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = ApproveShortReturnsSerializer

    def post(self, request):
        _data = request.data
        # If request is from reporter server use code to find entry by user
        entry_by_id = self.request.META.get('HTTP_ENTRY_BY_ID', '')
        if entry_by_id and checkers.is_integer(entry_by_id):
            entry_by_id = int(entry_by_id)
        else:
            entry_by_id = self.request.user.id
        try:
            serializer = self.get_serializer(
                data=request.data,
                context={'request': request}
            )
            if serializer.is_valid(raise_exception=True):
                delivery_sheet = serializer.validated_data.get('delivery_sheet')
                approved_by_id = serializer.data.get('approved_by')
                is_draft_items_found, context = delivery_sheet.approve_short_return_by_delivery_sheet(
                    approved_by_id,
                    entry_by_id
                )
                if not is_draft_items_found:
                    response = {
                        "status": "Failed",
                        "message": "No Draft Returns Found"
                    }
                    response.update(**context)
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
                response = {
                    "status": "Success",
                    "message": "Successfully Approved Returns",
                    "delivery_sheet_id": delivery_sheet.id,
                    "partial_return_amount": context.get('partial_return_amount'),
                    "partial_return_unique_pharmacy": context.get('partial_return_unique_pharmacy'),
                    "full_return_amount": context.get('full_return_amount'),
                    "full_return_unique_pharmacy": context.get('full_return_unique_pharmacy'),
                    "total_short": context.get('total_short'),
                }
                response.update(**context)
                return Response(response, status=status.HTTP_201_CREATED)

        except Exception as exception:
            exception_str = exception.args[0] if exception.args else str(exception)
            content = {'error': '{}'.format(exception_str)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class ShortReturnLogRetrieveUpdateDestroy(RetrieveUpdateDestroyAPICustomView):
    def get_permissions(self):
        if self.request.method == 'DELETE':
            self.available_permission_classes = (
                StaffIsAdmin,
                IsSuperUser,
                StaffIsSalesManager,
                StaffIsFrontDeskProductReturn,
                StaffIsDistributionT3,
                StaffIsDistributionT2,
            )
        else:
            self.available_permission_classes = (
                StaffIsAdmin,
                IsSuperUser,
                StaffIsDistributionT2,
                StaffIsDistributionT3,
                StaffIsSalesManager,
                StaffIsFrontDeskProductReturn
            )
        return (CheckAnyPermission(),)
    lookup_field = 'alias'

    def get_queryset(self, related_fields=None, only_fields=None):
        return ShortReturnLog.objects.exclude(status=Status.INACTIVE).order_by('-pk')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ShortReturnLogModelSerializer.Details
        return ShortReturnLogModelSerializer.Update


class ShortLogList(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsFrontDeskProductReturn,
        StaffIsSalesManager,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ShortReturnLogModelSerializer.List
    filterset_class = ShortReturnLogListWithoutTypeFilter

    def get_queryset(self):
        return ShortReturnLog.objects.filter(
            type=ShortReturnLogType.SHORT
        ).exclude(
            status=Status.INACTIVE,
        ).select_related(
            'received_by',
            'order_by_organization',
            'approved_by',
        )


class ReturnLogList(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsDistributionT2,
        StaffIsFrontDeskProductReturn,
        StaffIsSalesManager,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ShortReturnLogModelSerializer.List
    filterset_class = ShortReturnLogListWithoutTypeFilter

    def get_queryset(self):
        return ShortReturnLog.objects.filter(
            type=ShortReturnLogType.RETURN
        ).exclude(
            status=Status.INACTIVE
        ).select_related(
            'received_by',
            'order_by_organization',
            'approved_by',
        )
