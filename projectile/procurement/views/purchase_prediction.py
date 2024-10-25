from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework.serializers import ValidationError
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from rest_framework import status

from common.pagination import CachedCountPageNumberPagination
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
    StaffIsProcurementOfficer,
    StaffIsProcurementBuyerWithSupplier,
    StaffIsDistributionT1,
    StaffIsProcurementManager,
    StaffIsProcurementCoordinator,
)
from core.models import ScriptFileStorage
from procurement.serializers.purchase_prediction import PurchasePredictionModelSerializer
from ..filters import PurchasePredictionListFilter
from ..models import PurchasePrediction


class PurchasePredictionListCreate(ListCreateAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementBuyerWithSupplier,
        StaffIsDistributionT1,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission, )
    filterset_class = PurchasePredictionListFilter
    pagination_class = CachedCountPageNumberPagination

    def get_queryset(self, related_fields=None, only_fields=None):
        if self.request.user.is_admin_or_super_admin_or_procurement_manager_or_procurement_coordinator():
            return super().get_queryset(related_fields, only_fields)
        else:
            return PurchasePrediction().get_all_actives().filter(is_locked=False)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PurchasePredictionModelSerializer.List
        return PurchasePredictionModelSerializer.List


class PurchasePredictionIsLockedUpdate(UpdateAPIView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsProcurementManager,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)

    serializer_class = PurchasePredictionModelSerializer.LockUpdateSerializer

    def get_object(self):
        try:
            # ScriptFileStorage model instance alias
            return get_object_or_404(
                PurchasePrediction().get_all_actives(),
                prediction_file__alias=self.kwargs.get("alias")
            )
        except PurchasePrediction.DoesNotExist:
            raise ValidationError("Couldn't find matching prediction with given alias")


class PopulatePurchasePredictionDataFromPredFile(CreateAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = PurchasePredictionModelSerializer.PopulateDataFromPredFile

    @transaction.atomic
    def post(self, request, *args, **kwargs):

        try:
            with transaction.atomic():
                serializer = PurchasePredictionModelSerializer.PopulateDataFromPredFile(
                    data=request.data, context={'request': request})
                if serializer.is_valid(raise_exception=True):
                    file_id = serializer.data.get('file', '')
                    try:
                        file_instance = ScriptFileStorage.objects.get(pk=file_id)
                        success, error_message, new_instance_count, failed_instance_count, total_count = file_instance.populate_prediction_data_from_file(
                            self.request.user.organization_id
                        )
                        if success:
                            response = {
                                'message': 'Success',
                                'new_instance_count': new_instance_count,
                                'failed_instance_count': failed_instance_count,
                                'total_instance_count': total_count,
                                'error': error_message,
                            }
                            return Response(
                                response,
                                status=status.HTTP_201_CREATED
                            )
                        response = {
                            'message': 'Failed',
                            'new_instance_count': new_instance_count,
                            'failed_instance_count': failed_instance_count,
                            'total_instance_count': total_count,
                            'error': error_message,
                        }
                        return Response(
                            response,
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    except Exception as exception:
                        exception_str = exception.args[0] if exception.args else str(exception)
                        content = {'error': '{}'.format(exception_str)}
                        return Response(content, status=status.HTTP_400_BAD_REQUEST)

        except Exception as exception:
            exception_str = exception.args[0] if exception.args else str(exception)
            content = {'error': '{}'.format(exception_str)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
