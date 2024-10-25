import decimal
import json
from math import cos, radians

from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.enums import Status
from core.models import Organization
from core.permissions import (
    StaffIsAdmin,
    CheckAnyPermission,
    StaffIsSalesCoordinator,
    StaffIsSalesManager,
    IsSuperUser,
    StaffIsDistributionT3,
    StaffIsTelemarketer,
)
from core.views.common_view import (
    ListAPICustomView,
    ListCreateAPICustomView,
    CreateAPICustomView,
    RetrieveUpdateDestroyAPICustomView
)
from ecommerce.models import OrderInvoiceGroup
from pharmacy.enums import OrderTrackingStatus
from ..custom_serializer.organization import OrganizationModelSerializer
from ..custom_serializer.organization_responsible_person import PossibleResponsiblePerson

from ..filters import PossibleResponsiblePersonForOrganization, OrderInvoiceGroupFilter
from ..serializers import OrganizationNetSalesSerializer


class OrganizationPossiblePrimaryResponsiblePerson(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)

    filterset_class = PossibleResponsiblePersonForOrganization

    def get_queryset(self):
        return Organization.objects.exclude(status=Status.INACTIVE)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PossibleResponsiblePerson.Post
        return PossibleResponsiblePerson.List


class OrganizationBulkUpdate(CreateAPICustomView):
    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsTelemarketer,
    )
    permission_classes = (CheckAnyPermission,)

    serializer_class = OrganizationModelSerializer.WriteForBulkUpdate

    def post(self, request, *args, **kwargs):
        try:
            request_data = request.data
            serializer = self.serializer_class(data=request_data, many=True)
            if serializer.is_valid(raise_exception=True):
                for data in serializer.validated_data:
                    organization = data.get('alias', None)

                    update_fields = []
                    referrer = data.get('referrer')
                    if referrer is not None:
                        organization.referrer = referrer
                        update_fields.append('referrer')

                    primary_responsible_person = data.get('primary_responsible_person')
                    if primary_responsible_person is not None:
                        organization.primary_responsible_person = primary_responsible_person
                        update_fields.append('primary_responsible_person')

                    secondary_responsible_person = data.get('secondary_responsible_person')
                    if secondary_responsible_person is not None:
                        organization.secondary_responsible_person = secondary_responsible_person
                        update_fields.append('secondary_responsible_person')

                    discount_factor = data.get("discount_factor")
                    if discount_factor is not None:
                        organization.discount_factor = discount_factor
                        update_fields.append("discount_factor")

                    has_dynamic_discount_factor = data.get("has_dynamic_discount_factor")
                    if has_dynamic_discount_factor is not None:
                        organization.has_dynamic_discount_factor = has_dynamic_discount_factor
                        update_fields.append("has_dynamic_discount_factor")

                    # Save the organization if any fields were updated
                    if update_fields:
                        organization.save(update_fields=update_fields)

            response = {
                "message": "Success"
            }
            return Response(response, status=status.HTTP_200_OK)
        except Exception as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class OrganizationLocationUpdate(RetrieveUpdateDestroyAPICustomView):
    permission_classes = (StaffIsAdmin,)
    lookup_field = 'alias'
    serializer_class = OrganizationModelSerializer.LocationOnly

    def get_queryset(self):
        return Organization.objects.filter(
            status=Status.ACTIVE
        ).only('id', 'alias', 'geo_location')


class CountOrganizationsByLocation(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationModelSerializer.LocationOnly

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        geo_location = serializer.validated_data.get("geo_location", {})
        max_distance = serializer.validated_data.get("max_distance", 0)

        if geo_location == {}:
            return Response(
                {
                    "details": "You must provide geo_location coordinates to get number of organization with same location"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        #get latitude and longitude from geo_location
        latitude = geo_location["currentPosition"]["latitude"]
        longitude = geo_location["currentPosition"]["longitude"]

        # Calculate the latitude and longitude boundaries for the search area range
        lat_distance = max_distance / 111000  # 1 degree of latitude ~ 111000 meters
        lon_distance = max_distance / (111000 * cos(radians(latitude)))  # 1 degree of longitude ~ 111000 meters (at equator)

        # Calculate the min and max latitude and longitude for the search area
        min_latitude = latitude - lat_distance
        max_latitude = latitude + lat_distance
        min_longitude = longitude - lon_distance
        max_longitude = longitude + lon_distance

        # Calculate number of shop/organization within the specified range
        number_of_organization = Organization().get_all_actives().only("id").filter(
            geo_location__currentPosition__latitude__range=[min_latitude, max_latitude],
            geo_location__currentPosition__longitude__range=[min_longitude, max_longitude],
        )
        count = number_of_organization.count()
        message = f"""Are you sure that this is the exact shop location?
        There are already {count} other shops with the exact same location marked.
        Please only tag the location when you are directly outside the shop"""

        return Response({'number_of_organization': count, "details": message.strip()}, status=status.HTTP_200_OK)


class OrganizationShortInfoList(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = OrganizationModelSerializer.Short
    queryset = Organization().get_all_actives().only(
        "id",
        "alias",
        "name",
        "status",
        "address",
        "contact_person",
        "primary_mobile",
    )

    def get_queryset(self, related_fields=None, only_fields=None):
        queryset = self.queryset
        organizations_ids = self.request.query_params.get("organization_ids", None)

        if organizations_ids is None:
            raise ValueError("You must sent organization id to get information")

        organizations_ids = organizations_ids.split(',')
        queryset = queryset.filter(
            id__in=organizations_ids
        )

        return queryset


class OrganizationGeoLocationInfoList(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsSalesManager,
        StaffIsTelemarketer,
        StaffIsSalesCoordinator,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = OrganizationModelSerializer.GeoLocationOnly
    pagination_class = None

    def get_queryset(self):
        return Organization.objects.exclude(geo_location={}).only(
            "name",
            "geo_location"
        )


class OrganizationNetSalesReport(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsSalesCoordinator,
        StaffIsSalesManager,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = OrganizationNetSalesSerializer
    filterset_class = OrderInvoiceGroupFilter

    def get_queryset(self):
        valid_statuses = [
            OrderTrackingStatus.DELIVERED,
            OrderTrackingStatus.COMPLETED,
            OrderTrackingStatus.PARITAL_DELIVERED,
            OrderTrackingStatus.PORTER_DELIVERED,
            OrderTrackingStatus.PORTER_PARTIAL_DELIVERED,
        ]

        invoice_groups = OrderInvoiceGroup().get_all_actives().filter(
            current_order_status__in=valid_statuses
        ).exclude(
            orders__isnull=True
        ).distinct()

        invoice_data = invoice_groups.order_by().values(
            "order_by_organization",
            "order_by_organization__name",
            "order_by_organization__primary_mobile"
        ).annotate(
            id=F("order_by_organization"),
            name=F("order_by_organization__name"),
            mobile=F("order_by_organization__primary_mobile"),
            total_amount=Coalesce(
                Sum("sub_total"), decimal.Decimal(0)
            ) - Coalesce(
                Sum("discount"), decimal.Decimal(0)
            ) - Coalesce(
                Sum("additional_discount"), decimal.Decimal(0)
            ) + Coalesce(
                Sum("round_discount"), decimal.Decimal(0)
            ) + Coalesce(
                Sum("additional_cost"), decimal.Decimal(0)
            ) - Coalesce(
                Sum("total_short"), decimal.Decimal(0)
            ) - Coalesce(
                Sum("total_return"), decimal.Decimal(0)
            )

        )

        return invoice_data


class OrganizationHistory(RetrieveAPIView):
    """
    API endpoint to retrieve the organization history for an organization instance.
    This view provides a detailed changed history, including date, type of change,
    user who made the change, area discount factor
    and status over time.
    """

    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsTelemarketer,
        StaffIsDistributionT3,
        StaffIsSalesManager,
    )
    permission_classes = (CheckAnyPermission,)
    lookup_field = "alias"
    queryset = Organization().get_all_non_inactives()

    def get(self, request, *args, **kwargs):
        # get the organization instance
        instance = self.get_object()
        # retrieve all the changed history of the organization instance
        histories = instance.history.filter()
        history_data = []

        # Iter through organization histories
        for record in histories:
            record_data = {
                "date": record.history_date,
                "type": record.get_history_type_display(),
                "discount_factor": {
                    "current": record.discount_factor,
                    "previous": record.prev_record.discount_factor
                    if record.prev_record
                    else ""
                    if record.discount_factor
                    else "",
                },
                "has_dynamic_discount_factor": {
                    "current": record.has_dynamic_discount_factor,
                    "previous": record.prev_record.has_dynamic_discount_factor
                    if record.prev_record
                    else ""
                    if record.has_dynamic_discount_factor
                    else "",
                },
                "min_order_amount": {
                    "current": record.min_order_amount,
                    "previous": record.prev_record.min_order_amount
                    if record.prev_record
                    else ""
                    if record.min_order_amount
                    else "",
                },
                "updated_by":{
                    "id": record.history_user.id if record.history_user.id else "",
                    "code": record.history_user.code if record.history_user.code else "",
                    "alias": record.history_user.alias if record.history_user.alias else "",
                    "first_name": record.history_user.first_name if record.history_user.first_name else "",
                    "last_name": record.history_user.last_name if record.history_user.last_name else "",
                    "phone": record.history_user.phone if record.history_user.phone else ""
                },
                "status": {
                    "current": record.status,
                    "previous": record.prev_record.status if record.prev_record else "",
                },
                "area": {
                    "current": {
                        "alias": record.area.alias,
                        "name": record.area.name,
                        "code": record.area.code,
                        "discount_factor": record.area.discount_factor,
                    }
                    if record.area
                    else {},
                    "previous": {
                        "alias": record.area.alias,
                        "name": record.prev_record.area.name,
                        "code": record.prev_record.area.code,
                        "discount_factor": record.prev_record.area.discount_factor,
                    }
                    if record.prev_record and record.prev_record.area
                    else {},
                },
                "delivery_hub": {
                    "current": {
                        "alias": record.delivery_hub.alias,
                        "name": record.delivery_hub.name,
                        "short_code": record.delivery_hub.short_code,
                    }
                    if record.delivery_hub
                    else {},
                    "previous": {
                        "alias": record.delivery_hub.alias,
                        "name": record.delivery_hub.name,
                        "short_code": record.delivery_hub.short_code,
                    }
                    if record.prev_record and record.prev_record.delivery_hub
                    else {},
                },
                "phone": {
                    "current": record.primary_mobile,
                    "previous": record.prev_record.primary_mobile
                    if record.prev_record
                    else "",
                },
                "thana": {
                    "current": record.delivery_thana,
                    "previous": record.prev_record.delivery_thana
                    if record.prev_record
                    else "",
                },
            }
            history_data.append(record_data)

        return Response(
            history_data,
            status=status.HTTP_200_OK,
        )
