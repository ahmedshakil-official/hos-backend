import logging
import os
import time
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models.functions import TruncHour
from django.db.utils import IntegrityError
from django.db.models import Prefetch, Case, When, Value, IntegerField, Sum, DecimalField, F, Func, Count
from django.db.models.functions import Coalesce
from django.contrib.postgres.aggregates import JSONBAgg, ArrayAgg
from django.core.cache import cache
from django.utils import timezone
from rest_framework.response import Response
from django.utils.translation import gettext as _
# from rest_framework.generics import APIView
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.generics import (
    RetrieveUpdateAPIView,
    RetrieveAPIView,
    RetrieveDestroyAPIView,
    CreateAPIView,
)
from rest_framework.exceptions import APIException

from common.helpers import (
    custom_elastic_rebuild,
    generate_phone_no_for_sending_sms,
    to_boolean,
    versiontuple,
    get_date_from_period, get_date_time_from_period,
)
from common.utils import get_datetime_obj_from_datetime_str, generate_map_url_and_address_from_geo_data
from common.enums import Status
from common.cache_helpers import delete_qs_count_cache
from common.cache_keys import DUPLICATE_ORDER_REQUEST_CACHE_KEY_PREFIX, USER_HAS_CART_ITEM_CACHE_KEY_PREFIX
from common.tasks import (
    cache_expire_list,
    send_sms,
    send_same_sms_to_multiple_receivers,
    send_message_to_slack_or_mattermost_channel_lazy
)
from common.pagination import CachedCountPageNumberPagination

from core.permissions import (
    CheckAnyPermission,
    StaffIsAdmin,
    StaffIsMarketer,
    StaffIsProcurementOfficer,
    StaffIsSalesman,
    StaffIsReceptionist,
    IsSuperUser,
    StaffIsTrader,
    StaffIsReceptionist,
    IsOwner,
    StaffIsTelemarketer,
    StaffIsSalesCoordinator,
    StaffIsDeliveryHub,
    StaffIsDistributionT1,
    StaffIsDistributionT2,
    StaffIsDistributionT3,
    StaffIsFrontDeskProductReturn,
    StaffIsSalesManager,
)
from core.helpers import get_user_profile_details_from_cache
from core.models import Organization
from core.enums import OrganizationType
from core.views.common_view import ListCreateAPICustomView, CreateAPICustomView, ListAPICustomView
from expo_notification.tasks import send_push_notification_to_mobile_app
from ..custom_serializer.purchase import (
    DistributorOrderCartPostSerializer,
    DistributorOrderCartGetSerializer,
    DistributorOrderGroupPostSerializer,
    DistributorOrderListGetSerializer,
    DistributorOrderListSerializer,
    DistributorOrderDetailsGetForDistributorSerializer,
    DistributorOrderListGetSerializerForUser,
    ReorderSerializer,
    DistributorOrderCartGetV2Serializer,
    RequisitionRelatedPurchaseOrderProcurementSerializer, OrderPreOrderGraphListSerializer,
    NonGroupedOrderSerializer,
)

from ..custom_serializer.stock_io_log import (
    DistributorOrderCartPostV2Serializer,
    ProcessingToDeliverStockListSerializer,
)
from ..custom_serializer.order_tracking import (
    OrderTrackingModelSerializer,
)
from ..serializers import PurchaseBasicSerializer, DistributorOrderStateSerializer
from ..models import DistributorOrderGroup, Purchase, StockIOLog, Stock, OrderTracking
from ..enums import DistributorOrderType, PurchaseType, StorePointType, OrderTrackingStatus, SystemPlatforms
from ..filters import DistributorOrderListFilter
from ..utils import (
    send_push_notification_for_additional_discount,
    get_order_closing_info,
    get_cart_group_id,
)
from ..cart_helpers import update_cart, re_order
from ..cart_helpers_v2 import update_cart_v2

logger = logging.getLogger(__name__)

class DistributorOrderCartListCreate(ListCreateAPICustomView):

    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsSalesman,
        StaffIsAdmin
    )
    pagination_class = CachedCountPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DistributorOrderCartGetSerializer
        return DistributorOrderCartPostSerializer

    def get_queryset(self):
        # order_statuses = OrderTracking.objects.only('id')
        cart_items = StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization=self.request.user.organization_id
        ).select_related(
            'primary_unit',
            'secondary_unit',
            'stock__store_point',
            'stock__product__manufacturing_company',
            'stock__product__form',
            'stock__product__subgroup__product_group',
            'stock__product__generic',
            'stock__product__primary_unit',
            'stock__product__secondary_unit',
            'stock__product__category',
            'stock__product__compartment',
        ).only(
            'id',
            'alias',
            'status',
            'stock',
            'quantity',
            'rate',
            'batch',
            'base_discount',
            # 'expire_date',
            'date',
            # 'type',
            'primary_unit__id',
            'primary_unit__alias',
            'primary_unit__name',
            'primary_unit__description',
            # 'primary_unit__created_at',
            # 'primary_unit__updated_at',
            'secondary_unit__id',
            'secondary_unit__alias',
            'secondary_unit__name',
            'secondary_unit__description',
            # 'secondary_unit__created_at',
            # 'secondary_unit__updated_at',
            'discount_rate',
            'discount_total',
            'round_discount',
            'vat_rate',
            'vat_total',
            'tax_total',
            'tax_rate',
            # 'conversion_factor',
            # 'secondary_unit_flag',
            # 'data_entry_status',
            'purchase_id',
            'purchase__organization_id',
            'purchase__distributor__id',
            'purchase__distributor__alias',
            'purchase__distributor__name',
            'purchase__distributor__address',
            'purchase__distributor__delivery_sub_area',
            'purchase__distributor__delivery_thana',
            'purchase__distributor__primary_mobile',
            'purchase__distributor__status',
                'stock__id',
                'stock__alias',
                'stock__stock',
                'stock__demand',
                'stock__auto_adjustment',
                'stock__minimum_stock',
                'stock__rack',
                'stock__tracked',
                'stock__purchase_rate',
                'stock__calculated_price',
                'stock__order_rate',
                'stock__discount_margin',
                'stock__orderable_stock',
                    'stock__store_point__id',
                    'stock__store_point__alias',
                    'stock__store_point__name',
                    'stock__store_point__phone',
                    'stock__store_point__address',
                    'stock__store_point__type',
                    'stock__store_point__populate_global_product',
                    'stock__store_point__auto_adjustment',
                    'stock__store_point__created_at',
                    'stock__store_point__updated_at',
                    'stock__product__id',
                    'stock__product__code',
                    'stock__product__species',
                    'stock__product__alias',
                    'stock__product__name',
                    'stock__product__strength',
                    'stock__product__full_name',
                    'stock__product__description',
                    'stock__product__trading_price',
                    'stock__product__purchase_price',
                    'stock__product__status',
                    'stock__product__is_salesable',
                    'stock__product__is_service',
                    'stock__product__is_global',
                    'stock__product__conversion_factor',
                    'stock__product__category',
                    'stock__product__is_printable',
                    'stock__product__image',
                    'stock__product__unit_type',
                    'stock__product__order_limit_per_day',
                    'stock__product__discount_rate',
                    'stock__product__is_queueing_item',
                        'stock__product__manufacturing_company__id',
                        'stock__product__manufacturing_company__alias',
                        'stock__product__manufacturing_company__name',
                        'stock__product__manufacturing_company__description',
                        'stock__product__manufacturing_company__is_global',
                        'stock__product__form__id',
                        'stock__product__form__alias',
                        'stock__product__form__name',
                        'stock__product__form__description',
                        'stock__product__form__is_global',
                        'stock__product__subgroup__id',
                        'stock__product__subgroup__alias',
                        'stock__product__subgroup__name',
                        'stock__product__subgroup__description',
                        'stock__product__subgroup__is_global',
                            'stock__product__subgroup__product_group__id',
                            'stock__product__subgroup__product_group__alias',
                            'stock__product__subgroup__product_group__name',
                            'stock__product__subgroup__product_group__description',
                            'stock__product__subgroup__product_group__is_global',
                            'stock__product__subgroup__product_group__type',
                        'stock__product__generic__id',
                        'stock__product__generic__alias',
                        'stock__product__generic__name',
                        'stock__product__generic__description',
                        'stock__product__generic__is_global',
                        'stock__product__category__id',
                        'stock__product__category__alias',
                        'stock__product__category__name',
                        'stock__product__category__description',
                        'stock__product__category__is_global',
                        'stock__product__primary_unit__id',
                        'stock__product__primary_unit__alias',
                        'stock__product__primary_unit__name',
                        'stock__product__primary_unit__description',
                        'stock__product__secondary_unit__id',
                        'stock__product__secondary_unit__alias',
                        'stock__product__secondary_unit__name',
                        'stock__product__secondary_unit__description',
                        'stock__product__compartment__id',
                        'stock__product__compartment__alias',
                        'stock__product__compartment__name',
                        'stock__product__compartment__priority',
        )
        cart_queryset = Purchase.objects.prefetch_related(
            Prefetch('stock_io_logs', queryset=cart_items),
            # Prefetch('order_status', queryset=order_statuses)
        ).select_related(
            'distributor',
        ).filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization=self.request.user.organization_id,
            distributor_order_type=DistributorOrderType.CART,
            purchase_type=PurchaseType.VENDOR_ORDER,
            stock_io_logs__status=Status.DISTRIBUTOR_ORDER
        ).only(
            'id',
            'alias',
            'status',
            'purchase_date',
            'amount',
            'discount',
            'discount_rate',
            'round_discount',
            'vat_rate',
            'vat_total',
            'tax_rate',
            'tax_total',
            'grand_total',
            'receiver_id',
            'store_point_id',
            'person_organization_receiver_id',
            'distributor_order_group_id',
            'current_order_status',
            'tentative_delivery_date',
            'is_queueing_order',
            'additional_discount',
            'additional_discount_rate',
            'additional_cost',
            'additional_cost_rate',
            'order_rating',
            'order_rating_comment',
            'dynamic_discount_amount',
            'distributor__id',
            'distributor__alias',
            'distributor__name',
            'distributor__status',
            'distributor__address',
            'distributor__primary_mobile',
            'distributor__delivery_sub_area',
            'distributor__delivery_thana',
        ).distinct()
        queryset = DistributorOrderGroup.objects.prefetch_related(
            Prefetch('order_groups', queryset=cart_queryset)
        ).select_related(
            'organization'
        ).filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id,
            order_type=DistributorOrderType.CART
        ).only(
            'id',
            'alias',
            'status',
            'sub_total',
            'discount',
            'round_discount',
            'organization__id',
            'organization__alias',
            'organization__name',
            'organization__status',
            'organization__min_order_amount',
        )
        return queryset.order_by('-pk')


    def remove_cart_item(self, stock_io_alias=''):
        try:
            item = StockIOLog.objects.only(
                'id',
                'status'
            ).filter(
                alias=stock_io_alias,
            ).update(status=Status.INACTIVE)
            update_cart(self.request.user.organization_id, self.request.user.id)
            response = DistributorOrderCartGetSerializer(self.get_queryset().first(), context={'request': self.request})
            return Response(response.data, status=status.HTTP_200_OK)
        except Exception as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def post(self, request):
        try:
            orders = request.data
            organization_id = self.request.user.organization_id
            cart_group_id = get_cart_group_id(self.request.user.organization_id)

            cart_item_cache_key = f"{USER_HAS_CART_ITEM_CACHE_KEY_PREFIX}{organization_id}_{cart_group_id}"
            existing_cache = cache.get(cart_item_cache_key)

            # delete existing cache for user cart items
            if existing_cache:
                cache.delete(cart_item_cache_key)

            # List of cart item stock alias need to be removed
            removed_cart_item_stock_io = orders.pop('removed_cart_item_stock_io_alias', '')
            if removed_cart_item_stock_io:
                return self.remove_cart_item(removed_cart_item_stock_io)

            if not orders:
                is_order_disabled, message = get_order_closing_info()
                if is_order_disabled:
                    self.request.user.organization.clear_cart()
                    return Response({}, status=status.HTTP_200_OK)
                update_cart(request.user.organization_id, self.request.user.id)
                response = DistributorOrderCartGetSerializer(self.get_queryset().first(), context={'request': self.request})
                return Response(response.data, status=status.HTTP_200_OK)

            # Separate the order/cart groups data
            cart_group = orders.pop('cart_group', [])

            serializer = DistributorOrderCartPostSerializer(
                data=orders,
                context={'request': request, 'cart_group': cart_group}
            )
            if serializer.is_valid(raise_exception=True):
                data = serializer.data
                stock_io_logs = data.get("stock_io_logs", [])
                # cart = serializer.save()
                # cart.distributor_order_group.update_order_amount()
                update_cart(
                    request.user.organization_id,
                    self.request.user.id,
                    stock_io_logs
                )
                # Populate es index
                # custom_elastic_rebuild('pharmacy.models.Purchase', {'id': cart.id})
                response = DistributorOrderCartGetSerializer(
                    self.get_queryset().first(), context={'request': self.request})

                return Response(
                    response.data,
                    status=status.HTTP_201_CREATED
                )

        except Exception as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class DistributorOrderCartCreateOrUpdate(DistributorOrderCartListCreate):

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DistributorOrderCartGetV2Serializer
        return DistributorOrderCartPostV2Serializer

    def get_queryset(self):
        cart_items = StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization=self.request.user.organization_id
        ).select_related(
            'primary_unit',
            'secondary_unit',
            'stock__product__manufacturing_company',
            'stock__product__form',
            'stock__product__subgroup__product_group',
            'stock__product__generic',
            'stock__product__primary_unit',
            'stock__product__secondary_unit',
            'stock__product__category',
        ).only(
            'id',
            'alias',
            'quantity',
            'rate',
            'date',
            'batch',
            'primary_unit__id',
            'primary_unit__alias',
            'primary_unit__name',
            'secondary_unit__id',
            'secondary_unit__alias',
            'secondary_unit__name',
            'discount_rate',
            'discount_total',
            'round_discount',
            'conversion_factor',
            'secondary_unit_flag',
            'purchase_id',
            'stock__id',
            'stock__alias',
                'stock__store_point__id',
                'stock__product__id',
                'stock__product__code',
                'stock__product__species',
                'stock__product__alias',
                'stock__product__name',
                'stock__product__strength',
                'stock__product__full_name',
                'stock__product__description',
                'stock__product__trading_price',
                'stock__product__purchase_price',
                'stock__product__status',
                'stock__product__is_salesable',
                'stock__product__is_service',
                'stock__product__is_global',
                'stock__product__conversion_factor',
                'stock__product__category',
                'stock__product__is_printable',
                'stock__product__image',
                'stock__product__order_limit_per_day',
                'stock__product__discount_rate',
                'stock__product__is_queueing_item',
                    'stock__product__manufacturing_company__id',
                    'stock__product__manufacturing_company__alias',
                    'stock__product__manufacturing_company__name',
                    'stock__product__manufacturing_company__description',
                    'stock__product__manufacturing_company__is_global',
                    'stock__product__form__id',
                    'stock__product__form__alias',
                    'stock__product__form__name',
                    'stock__product__form__description',
                    'stock__product__form__is_global',
                    'stock__product__subgroup__id',
                    'stock__product__subgroup__alias',
                    'stock__product__subgroup__name',
                    'stock__product__subgroup__description',
                    'stock__product__subgroup__is_global',
                        'stock__product__subgroup__product_group__id',
                        'stock__product__subgroup__product_group__alias',
                        'stock__product__subgroup__product_group__name',
                        'stock__product__subgroup__product_group__description',
                        'stock__product__subgroup__product_group__is_global',
                        'stock__product__subgroup__product_group__type',
                    'stock__product__generic__id',
                    'stock__product__generic__alias',
                    'stock__product__generic__name',
                    'stock__product__generic__description',
                    'stock__product__generic__is_global',
                    'stock__product__category__id',
                    'stock__product__category__alias',
                    'stock__product__category__name',
                    'stock__product__category__description',
                    'stock__product__category__is_global',
                    'stock__product__primary_unit__id',
                    'stock__product__primary_unit__alias',
                    'stock__product__primary_unit__name',
                    'stock__product__primary_unit__description',
                    'stock__product__primary_unit__created_at',
                    'stock__product__primary_unit__updated_at',
                    'stock__product__secondary_unit__id',
                    'stock__product__secondary_unit__alias',
                    'stock__product__secondary_unit__name',
                    'stock__product__secondary_unit__description',
                    'stock__product__secondary_unit__created_at',
                    'stock__product__secondary_unit__updated_at',
                    'stock__product__compartment__id',
                    'stock__product__compartment__alias',
                    'stock__product__compartment__name',
                    'stock__product__compartment__priority',
        )
        cart_queryset = Purchase.objects.prefetch_related(
            Prefetch('stock_io_logs', queryset=cart_items),
        ).select_related(
            'distributor',
        ).filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization=self.request.user.organization_id,
            distributor_order_type=DistributorOrderType.CART,
            purchase_type=PurchaseType.VENDOR_ORDER,
            stock_io_logs__status=Status.DISTRIBUTOR_ORDER
        ).only(
            'id',
            'alias',
            'status',
            'purchase_date',
            'amount',
            'discount',
            'discount_rate',
            'round_discount',
            'grand_total',
            'store_point_id',
            'distributor_order_group_id',
            'tentative_delivery_date',
            'is_queueing_order',
            'distributor__id',
            'distributor__alias',
            'distributor__name',
            'distributor__status',
            'distributor__address',
            'distributor__primary_mobile',
            'distributor__delivery_sub_area',
            'distributor__delivery_thana',
        ).distinct()
        queryset = DistributorOrderGroup.objects.prefetch_related(
            Prefetch('order_groups', queryset=cart_queryset)
        ).select_related(
            'organization'
        ).filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id,
            order_type=DistributorOrderType.CART
        ).only(
            'id',
            'alias',
            'status',
            'sub_total',
            'discount',
            'round_discount',
            'organization__id',
            'organization__alias',
            'organization__name',
            'organization__status',
            'organization__min_order_amount',
        )
        return queryset.order_by('-pk')

    def remove_cart_item(self, stock_io_alias=''):
        try:
            item = StockIOLog.objects.only(
                'id',
                'status'
            ).filter(
                alias=stock_io_alias,
            )
            item.update(status=Status.INACTIVE)
            update_cart_v2(self.request.user.organization_id, self.request.user.id)
            response = DistributorOrderCartGetV2Serializer(
                    self.get_queryset().first(), context={'request': self.request})
            return Response(response.data, status=status.HTTP_200_OK)
        except Exception as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def post(self, request):
        try:
            orders = request.data

            # List of cart item stock alias need to be removed
            removed_cart_item_stock_io = orders.pop('removed_cart_item_stock_io_alias', '')
            if removed_cart_item_stock_io:
                return self.remove_cart_item(removed_cart_item_stock_io)

            if orders:
                serializer = DistributorOrderCartPostV2Serializer(
                    data=orders,
                    context={'request': request,}
                )
                if serializer.is_valid(raise_exception=True):
                    cart = serializer.save()
                    update_cart_v2(
                        org_id=request.user.organization_id,
                        user_id=self.request.user.id,
                    )
                    response = DistributorOrderCartGetV2Serializer(
                        self.get_queryset().first(), context={'request': self.request})

                    return Response(
                        response.data,
                        status=status.HTTP_201_CREATED
                    )
            else:
                update_cart_v2(request.user.organization_id, self.request.user.id)
                response = DistributorOrderCartGetV2Serializer(self.get_queryset().first(), context={'request': self.request})
                return Response(response.data, status=status.HTTP_200_OK)

        except Exception as exception:
            exception_str = exception.args[0] if exception.args else str(exception)
            content = {'error': '{}'.format(exception_str)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class DistributorReOrder(DistributorOrderCartListCreate):

    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsSalesman,
        StaffIsAdmin
    )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DistributorOrderCartGetSerializer
        return ReorderSerializer


    def post(self, request):
        try:
            reorder_data = request.data

            serializer = ReorderSerializer(
                data=reorder_data,
                context={'request': request,}
            )
            if serializer.is_valid(raise_exception=True):
                order_id = serializer.data.get('order', None)
                clear_cart = serializer.data.get('clear_cart', False)
                re_order(
                    request.user.organization_id,
                    self.request.user.id,
                    order_id,
                    clear_cart
                )

                response = DistributorOrderCartGetSerializer(
                    self.get_queryset().first(), context={'request': self.request})

                return Response(
                    response.data,
                    status=status.HTTP_201_CREATED
                )

        except Exception as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class DistributorOrderDetails(RetrieveUpdateAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
        StaffIsReceptionist,
        StaffIsTelemarketer,
        StaffIsMarketer,
        StaffIsDeliveryHub,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsFrontDeskProductReturn,
        StaffIsSalesManager,
    )
    permission_classes = (CheckAnyPermission, )

    lookup_field = 'alias'

    def get_queryset(self):
        is_distributor = self.request.user.profile_details.organization.type == OrganizationType.DISTRIBUTOR
        order_items = StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            # organization=self.request.user.organization
        ).select_related(
            'primary_unit',
            'secondary_unit',
            # 'stock__product',
            'stock__store_point',
            'stock__product__manufacturing_company',
            'stock__product__form',
            'stock__product__subgroup__product_group',
            'stock__product__generic',
            'stock__product__primary_unit',
            'stock__product__secondary_unit',
            'stock__product__category',
        ).only(
            'id',
            'alias',
            'status',
            'stock',
            'quantity',
            'rate',
            'batch',
            'expire_date',
            'date',
            'type',
            'primary_unit__id',
            'primary_unit__alias',
            'primary_unit__name',
            'primary_unit__description',
            'primary_unit__created_at',
            'primary_unit__updated_at',
            'secondary_unit__id',
            'secondary_unit__alias',
            'secondary_unit__name',
            'secondary_unit__description',
            'secondary_unit__created_at',
            'secondary_unit__updated_at',
            'discount_rate',
            'discount_total',
            'round_discount',
            'vat_rate',
            'vat_total',
            'tax_total',
            'tax_rate',
            'conversion_factor',
            'secondary_unit_flag',
            'data_entry_status',
            'purchase_id',
                'stock__id',
                'stock__alias',
                'stock__stock',
                'stock__demand',
                'stock__auto_adjustment',
                'stock__minimum_stock',
                'stock__rack',
                'stock__tracked',
                'stock__purchase_rate',
                'stock__calculated_price',
                'stock__order_rate',
                'stock__discount_margin',
                    'stock__store_point__id',
                    'stock__store_point__alias',
                    'stock__store_point__name',
                    'stock__store_point__phone',
                    'stock__store_point__address',
                    'stock__store_point__type',
                    'stock__store_point__populate_global_product',
                    'stock__store_point__auto_adjustment',
                    'stock__store_point__created_at',
                    'stock__store_point__updated_at',
                    'stock__product__id',
                    'stock__product__code',
                    'stock__product__species',
                    'stock__product__alias',
                    'stock__product__name',
                    'stock__product__strength',
                    'stock__product__full_name',
                    'stock__product__description',
                    'stock__product__trading_price',
                    'stock__product__purchase_price',
                    'stock__product__status',
                    'stock__product__is_salesable',
                    'stock__product__is_service',
                    'stock__product__is_global',
                    'stock__product__conversion_factor',
                    'stock__product__category',
                    'stock__product__is_printable',
                    'stock__product__image',
                    'stock__product__order_limit_per_day',
                    'stock__product__discount_rate',
                        'stock__product__manufacturing_company__id',
                        'stock__product__manufacturing_company__alias',
                        'stock__product__manufacturing_company__name',
                        'stock__product__manufacturing_company__description',
                        'stock__product__manufacturing_company__is_global',
                        'stock__product__form__id',
                        'stock__product__form__alias',
                        'stock__product__form__name',
                        'stock__product__form__description',
                        'stock__product__form__is_global',
                        'stock__product__subgroup__id',
                        'stock__product__subgroup__alias',
                        'stock__product__subgroup__name',
                        'stock__product__subgroup__description',
                        'stock__product__subgroup__is_global',
                            'stock__product__subgroup__product_group__id',
                            'stock__product__subgroup__product_group__alias',
                            'stock__product__subgroup__product_group__name',
                            'stock__product__subgroup__product_group__description',
                            'stock__product__subgroup__product_group__is_global',
                            'stock__product__subgroup__product_group__type',
                        'stock__product__generic__id',
                        'stock__product__generic__alias',
                        'stock__product__generic__name',
                        'stock__product__generic__description',
                        'stock__product__generic__is_global',
                        'stock__product__category__id',
                        'stock__product__category__alias',
                        'stock__product__category__name',
                        'stock__product__category__description',
                        'stock__product__category__is_global',
                        'stock__product__primary_unit__id',
                        'stock__product__primary_unit__alias',
                        'stock__product__primary_unit__name',
                        'stock__product__primary_unit__description',
                        'stock__product__secondary_unit__id',
                        'stock__product__secondary_unit__alias',
                        'stock__product__secondary_unit__name',
                        'stock__product__secondary_unit__description',
        ).order_by('stock__product_full_name')

        if is_distributor:
            queryset = Purchase.objects.prefetch_related(
                Prefetch('stock_io_logs', queryset=order_items)
            ).filter(
                status=Status.DISTRIBUTOR_ORDER,
                distributor=self.request.user.organization_id,
                distributor_order_type=DistributorOrderType.ORDER,
                purchase_type=PurchaseType.VENDOR_ORDER,
            ).select_related(
                'distributor',
                'organization',
            ).only(
                'id',
                'alias',
                'status',
                'purchase_date',
                'amount',
                'discount',
                'discount_rate',
                'round_discount',
                'vat_rate',
                'vat_total',
                'tax_rate',
                'tax_total',
                'grand_total',
                'invoice_group',
                'order_rating',
                'order_rating_comment',
                'additional_discount',
                'additional_discount_rate',
                'additional_cost',
                'additional_cost_rate',
                'distributor__id',
                'distributor__alias',
                'distributor__name',
                'distributor__status',
                'distributor__address',
                'distributor__primary_mobile',
                'organization__id',
                'organization__alias',
                'organization__name',
                'organization__status',
                'organization__address',
                'organization__primary_mobile',
            )
            return queryset

        cart_queryset = Purchase.objects.prefetch_related(
            Prefetch('stock_io_logs', queryset=order_items),
            Prefetch('order_status')
        ).select_related(
            'distributor',
        ).filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization=self.request.user.organization_id,
            distributor_order_type=DistributorOrderType.ORDER,
            purchase_type=PurchaseType.VENDOR_ORDER,
        ).only(
            'id',
            'alias',
            'status',
            'purchase_date',
            'amount',
            'discount',
            'discount_rate',
            'round_discount',
            'vat_rate',
            'vat_total',
            'tax_rate',
            'tax_total',
            'grand_total',
            'order_rating',
            'order_rating_comment',
            'distributor_order_group_id',
            'current_order_status',
            'additional_discount',
            'additional_discount_rate',
            'additional_cost',
            'additional_cost_rate',
            'distributor__id',
            'distributor__alias',
            'distributor__name',
            'distributor__status',
            'distributor__address',
            'distributor__primary_mobile',
        )

        queryset = DistributorOrderGroup.objects.prefetch_related(
            Prefetch('order_groups', queryset=cart_queryset)
        ).select_related(
            'organization',
        ).filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id,
            order_type=DistributorOrderType.ORDER
        ).only(
            'id',
            'alias',
            'status',
            'sub_total',
            'discount',
            'round_discount',
            'organization__id',
            'organization__alias',
            'organization__name',
            'organization__status',
            'organization__min_order_amount',
        )
        return queryset

    def get_serializer_class(self):
        is_distributor = self.request.user.profile_details.organization.type == OrganizationType.DISTRIBUTOR
        if self.request.method == 'GET' and not is_distributor:
            return DistributorOrderCartGetSerializer
        return DistributorOrderDetailsGetForDistributorSerializer

    def perform_update(self, serializer, extra_fields=None):
        self.create_data = {}
        tentative_delivery_date = self.request.data.get('tentative_delivery_date', None)
        additional_discount = self.request.data.get('additional_discount', 0)
        additional_discount_rate = self.request.data.get('additional_discount_rate', 0)
        if tentative_delivery_date:
            tracking_statuses = OrderTracking.objects.filter(
                status=Status.ACTIVE,
                order=self.get_object()
            ).exclude(
                order_status__in=[OrderTrackingStatus.IN_QUEUE, OrderTrackingStatus.PENDING, OrderTrackingStatus.ACCEPTED]
            )
            if tracking_statuses.exists():
                raise APIException("Updating delivery date is not allowed.")
        if hasattr(serializer.Meta.model, 'updated_by'):
            self.create_data['updated_by_id'] = self.request.user.id

        if extra_fields is not None:
            self.add_extra_fields(extra_fields)

        order = serializer.save(**self.create_data)
        send_push_notification_for_additional_discount(
            order.entry_by_id,
            self.request.user.id,
            additional_discount,
            order.id
        )
        order.distributor_order_group.update_order_amount(order=True)


class DistributorOrderListCreate(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsSalesman,
        StaffIsAdmin,
        StaffIsTrader,
        StaffIsReceptionist,
        StaffIsMarketer,
        StaffIsSalesCoordinator,
        StaffIsDeliveryHub,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsFrontDeskProductReturn,
        StaffIsSalesManager,
        StaffIsTelemarketer,
    )
    permission_classes = (CheckAnyPermission, )
    filterset_class = DistributorOrderListFilter
    pagination_class = CachedCountPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DistributorOrderListGetSerializer
        return DistributorOrderGroupPostSerializer

    def get_queryset(self):
        is_distributor = self.request.user.profile_details.organization.type == OrganizationType.DISTRIBUTOR
        is_trader = StaffIsTrader().has_permission(self.request, DistributorOrderListCreate)
        order_by_area_subarea = to_boolean(self.request.query_params.get('order_by_area_subarea', False))
        filters = {
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER
        }
        if is_distributor:
            filters['distributor'] = self.request.user.organization_id
            if is_trader:
                filters['organization__entry_by__id'] = self.request.user.id
        else:
            filters['organization'] = self.request.user.organization_id
        order_queryset = Purchase.objects.select_related(
            'organization__entry_by',
            "distributor_order_group",
            'responsible_employee__designation__department',
        ).filter(
            **filters
        ).select_related(
            'organization'
        ).distinct()
        if order_by_area_subarea:
            return order_queryset.order_by('organization__delivery_thana', 'organization__delivery_sub_area')
        return order_queryset.order_by('-pk')

    def list(self, request, *args, **kwargs):
        is_distributor = self.request.user.profile_details.organization.type == OrganizationType.DISTRIBUTOR
        queryset = self.get_queryset()
        queryset = self.filterset_class(request.GET, queryset).qs
        id_of_queryset = queryset.values_list('id', flat=True)
        response_data = self.get_from_cache(
            queryset=id_of_queryset,
            request=request,
            cache_key='purchase_distributor_order',
            response_only=True
        )

        if is_distributor:
            return self.get_paginated_response(response_data)
        serialized_data = DistributorOrderListGetSerializerForUser(response_data, many=True).data
        return self.get_paginated_response(serialized_data)

    def remove_items_from_cart(self):
        # Get cart group id from cache
        cart_group_id = get_cart_group_id(self.request.user.organization_id)
        # try:
        #     user_organization = Organization.objects.only('id').get(
        #         pk=self.request.user.organization_id,
        #     )
        #     cart_group = user_organization.get_or_add_cart_group(
        #         only_fields=['id',]
        #     )
        # except:
        #     cart_group = self.request.user.organization.get_or_add_cart_group()
        cart_items = StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization__id=self.request.user.organization_id,
            purchase__distributor_order_type=DistributorOrderType.CART,
            purchase__distributor_order_group__order_type=DistributorOrderType.CART,
            purchase__distributor_order_group__id=cart_group_id
        ).only(
            'id',
            'status',
        ).update(status=Status.INACTIVE)

    def send_sms_to_customer_and_distributor(self, order_group, _orders):
        try:
            system_platform = int(
                self.request.META.get("HTTP_X_SYSTEM_PLATFORM", SystemPlatforms.ANDROID_APP))
            app_version = self.request.headers.get('X-App-Version', '')
            user_details = get_user_profile_details_from_cache(self.request.user.id)
            customer_mobile = generate_phone_no_for_sending_sms(
                user_details.phone
            )
            # Send sms to customer
            if customer_mobile and system_platform != SystemPlatforms.ANDROID_APP:
                try:
                    customer_name = user_details.organization.contact_person
                except:
                    customer_name = "User"
                orders = ", ".join(list(map(lambda order: f"#{order.get('id')}", _orders)))
                customer_sms_text = "Hi {}, \nThank you for your order {}. Keep using HealthOS and get exciting offers.".format(
                    customer_name,
                    orders
                )
                send_sms.delay(
                    customer_mobile,
                    customer_sms_text,
                    self.request.user.organization_id
                )
            # orders = list(Purchase.objects.filter(
            #     distributor_order_group__group_id=order_group.group_id,
            #     status=Status.DISTRIBUTOR_ORDER,
            #     distributor_order_type=DistributorOrderType.ORDER,
            #     purchase_type=PurchaseType.VENDOR_ORDER,
            # ).values_list('pk', flat=True))
            # orders = ", ".join(list(map(lambda order: f"#{order.get('id')}", _orders)))
            # customer_sms_text = "Hi {}, \nThank you for your order {}. Keep using HealthOS and get exciting offers.".format(
            #     customer_name,
            #     orders
            # )
            # # Send sms to customer
            # if customer_mobile and system_platform != SystemPlatforms.ANDROID_APP:
            #     send_sms.delay(customer_mobile, customer_sms_text, order_group.organization_id)

            # phone_numbers = os.environ.get('NUMBERS_FOR_RECEIVING_ORDER_MESSAGE', '')
            orders = ", ".join(list(map(lambda order: f"#{order.get('id')}", _orders)))
            distributor_sms_text = "New order {} received from {}, Amount BDT {} Contact no: {}.".format(
                orders,
                user_details.organization.name,
                order_group.total_payable_amount,
                customer_mobile
            )
            # if phone_numbers:
            #     phone_numbers = phone_numbers.split(',') if phone_numbers else []
            #     phone_numbers = ", ".join(
            #         list(map(lambda phone: "880{}".format(phone[-10:]), phone_numbers)))
            #     phone_numbers = [item.strip() for item in phone_numbers.split(',')]
            #     # Send sms to support
            #     send_same_sms_to_multiple_receivers.delay(phone_numbers, distributor_sms_text)
            # Send message to slack channel
            # orders_alias = list(Purchase.objects.filter(
            #     distributor_order_group__group_id=order_group.group_id,
            #     status=Status.DISTRIBUTOR_ORDER,
            #     distributor_order_type=DistributorOrderType.ORDER,
            #     purchase_type=PurchaseType.VENDOR_ORDER,
            # ).values_list('alias', flat=True))
            base_url = "https://lh.healthosbd.com"
            # base_url = "http://localhost:8000"
            urls = []
            for item in _orders:
                urls.append(f"{base_url}/#!/cart-order-details/{item.get('alias')}")
            map_address = generate_map_url_and_address_from_geo_data(self.request.headers)
            slack_message = "{}\nDetails: {},\nAddress: {}(Approx.)\nGoogle Map: {}".format(
                distributor_sms_text,
                " , ".join(urls),
                map_address.get("address", "Not Found"),
                map_address.get("map_url", "Not Found")
            )
            send_message_to_slack_or_mattermost_channel_lazy.delay(
                os.environ.get('HOS_PHARMA_CHANNEL_ID', ""),
                slack_message
            )

            # Send push for older version of app
            if system_platform == SystemPlatforms.ANDROID_APP and versiontuple(app_version) < versiontuple("1.19.0"):
                notification_title = "অ্যাপ আপডেট !!!"
                notification_body = "আপনার অ্যাপ ভার্সনটি আপডেট না হওয়ায় নতুন ফিচারগুলো থেকে বঞ্চিত হচ্ছেন, অনুগ্রহপূর্বক অ্যাপটি আপডেট করুন ।"
                notification_data = {}
                # Send push notification to mobile device
                send_push_notification_to_mobile_app.delay(
                    self.request.user.id,
                    title=notification_title,
                    body=notification_body,
                    data=notification_data,
                    entry_by_id=self.request.user.id
                )
        except:
            pass

    @transaction.atomic
    def post(self, request):
        organization_id = self.request.user.organization_id
        cache_key = DUPLICATE_ORDER_REQUEST_CACHE_KEY_PREFIX + str(organization_id)

        cart_group_id = get_cart_group_id(self.request.user.organization_id)
        cart_item_cache_key = f"{USER_HAS_CART_ITEM_CACHE_KEY_PREFIX}{organization_id}_{cart_group_id}"

        request_data = request.data
        if not request_data:
            error = {
                "error": "Request data is empty."
            }
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        is_order_disabled, message = get_order_closing_info()
        if is_order_disabled:
            error = {
                "detail": message,
                "error": message
            }
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        is_org_active = self.request.user.profile_details.organization.status == Status.ACTIVE
        if not is_org_active:
            error = {
                "error": "Sorry, Your account is inactive or suspended, please call helpline for further details."
            }
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer = DistributorOrderGroupPostSerializer(
                data=request_data,
                context={'request': request}
            )
            if serializer.is_valid(raise_exception=True):
                # Check for duplicate request
                if cache.get(cache_key):
                    error = {
                        "error": "Your order is on the possess please wait!"
                    }
                    return Response(error, status=status.HTTP_400_BAD_REQUEST)
                # Set the cache key to prevent further duplicate requests
                cache.set(key=cache_key, value=True, timeout=1800)
                logger.info(f"add cache key for duplicate order request_{organization_id}.")

                # Empty cart item order
                if cache.get(cart_item_cache_key):
                    error = {
                        "error": "Your cart is empty!"
                    }
                    return Response(error, status=status.HTTP_400_BAD_REQUEST)
                cache.set(key=cart_item_cache_key, value=True, timeout=1800)
                logger.info(f"Add cache key for order request without cart_{cart_group_id}.")

                order_group = serializer.save()
                order_id_list = serializer.order_id_list
                # Remove items from cart
                self.remove_items_from_cart()

                # Query order data
                order_data = list(Purchase.objects.filter(
                    pk__in=order_id_list
                ).values(
                    'id',
                    'alias',
                    'tentative_delivery_date',
                    'is_queueing_order',
                ))
                # Send SMS to customer and support
                self.send_sms_to_customer_and_distributor(order_group, order_data)
                # Prepare response data
                response_data = {
                    "message": "Success",
                    "orders": order_data
                }
                # Populate ES index
                custom_elastic_rebuild(
                    'pharmacy.models.Purchase', {'distributor_order_group__group_id': order_group.group_id})
                # Delete QS count cache
                delete_qs_count_cache(Purchase)
                return Response(
                    response_data,
                    status=status.HTTP_201_CREATED
                )

        except Exception as exception:
            # Handle exceptions, log errors, and return an appropriate response
            exception_str = exception.args[0] if exception.args else str(exception)
            if isinstance(exception_str, dict):
                content = {
                    'error': exception_str
                }
            else:
                content = {'error': '{}'.format(exception_str)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        finally:
            # Delete the cache key after processing the request
            cache.delete(cache_key)
            logger.info(f"removed cache key for duplicate order request_{organization_id}.")
        return Response(status=status.HTTP_400_BAD_REQUEST)


class DistributorOrderStatusChangeLogList(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsTelemarketer,
        StaffIsDeliveryHub,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsFrontDeskProductReturn,
        StaffIsSalesCoordinator,
        StaffIsSalesManager,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = OrderTrackingModelSerializer.ListWithEntryBy

    def get_queryset(self, related_fields=None, only_fields=None):
        order_alias = self.kwargs.get("alias", None)
        queryset = OrderTracking().get_all_actives().filter(
            order__alias=order_alias
        ).select_related(
            "entry_by",
        ).only(
            "id",
            "alias",
            "date",
            "remarks",
            "order_id",
            "failed_delivery_reason",
            "order_status",
            "entry_by__id",
            "entry_by__alias",
            "entry_by__code",
            "entry_by__phone",
            "entry_by__first_name",
            "entry_by__last_name",
        )

        return queryset


class DistributorNonGroupedOrderList(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsTelemarketer,
        StaffIsDeliveryHub,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsFrontDeskProductReturn,
        StaffIsSalesCoordinator,
        StaffIsSalesManager,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = NonGroupedOrderSerializer
    filterset_class = DistributorOrderListFilter

    def get_queryset(self, related_fields=None, only_fields=None):
        filters = {
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER
        }
        queryset = Purchase.objects.filter(
            **filters,
            invoice_group__isnull=True
        ).select_related("organization").values("organization").annotate(
            alias = F("organization__alias"),
            name = F("organization__name"),
            orders = JSONBAgg(
                Func(
                    Value("id"), "id",
                    Value("is_queueing_order"), "is_queueing_order",
                    Value("order_date"), "purchase_date",
                    Value("delivery_date"), "tentative_delivery_date",
                    Value("amount"), "amount",
                    Value("discount"), "discount",
                    Value("grand_total"), "grand_total",
                    function="json_build_object"
                )
            ),
            total_amount = Coalesce(Sum(F("amount")), 0.00, output_field=DecimalField()),
            total_discount = Coalesce(Sum(F("discount")), 0.00, output_field=DecimalField()),
            grand_totals = Coalesce(Sum(F("grand_total")), 0.00, output_field=DecimalField()),
        )

        return queryset


class DistributorOrderStats(APIView):

    available_permission_classes = (
        IsSuperUser,
    )
    permission_classes = (CheckAnyPermission,)


    def get(self, request):
        data = Stock.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization,
            store_point__type=StorePointType.VENDOR_DEFAULT,
            product__is_published=True
        )
        response_data = DistributorOrderStateSerializer(data, many=True).data

        return Response(response_data, status=status.HTTP_200_OK)


class OrderStatusResponsiblePersonBulkCreate(CreateAPICustomView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission,)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        data = request.data
        order_ids = data.get('order_ids', [])
        responsible_employee = data.get('responsible_employee', "")
        status_data = data.get('order_status_data', [])
        tracking_status = None
        if status_data:
            tracking_status = status_data[0].get('order_status', None)

        try:
            with transaction.atomic():
                if status_data and order_ids:
                    # Update order status and responsible person
                    queryset = Purchase.objects.filter(pk__in=order_ids)
                    update_fields = ['responsible_employee', 'updated_by']
                    if responsible_employee:
                        for order in queryset:
                            order.responsible_employee_id=responsible_employee
                            order.updated_by_id=self.request.user.id
                            if tracking_status:
                                order.current_order_status = tracking_status
                                update_fields += ['current_order_status']
                            order.save(update_fields=update_fields)

                    serializer = OrderTrackingModelSerializer.List(
                        data=status_data,
                        many=True,
                        context={'request': request}
                    )
                    if serializer.is_valid(raise_exception=True):
                        serializer.save(
                            entry_by_id=self.request.user.id,
                        )
                    # Populate es index
                    custom_elastic_rebuild('pharmacy.models.Purchase', {'pk__in': order_ids})
                    # Delete redis cache
                    key_list = list(
                        map(
                            lambda item: 'purchase_distributor_order_{}'.format(str(item).zfill(12)),
                            order_ids
                        )
                    )

                    cache.delete_many(key_list)
                    # response = DistributorOrderListGetSerializer(
                    #     queryset,
                    #     context={'request': self.request},
                    #     many=True
                    # )
                    response = {
                        'message': 'Success',
                        'orders': list(queryset.values_list('pk', flat=True))
                    }
                    return Response(
                        # response.data,
                        response,
                        status=status.HTTP_201_CREATED
                    )
                elif responsible_employee and order_ids:
                    queryset = Purchase.objects.filter(pk__in=order_ids)
                    for order in queryset:
                        order.responsible_employee_id=responsible_employee
                        order.updated_by_id=self.request.user.id
                        order.save(update_fields=['responsible_employee', 'updated_by'])
                    # Populate es index
                    custom_elastic_rebuild('pharmacy.models.Purchase', {'pk__in': order_ids})
                    # Delete redis cache
                    key_list = list(
                        map(
                            lambda item: 'purchase_distributor_order_{}'.format(str(item).zfill(12)),
                            order_ids
                        )
                    )

                    cache.delete_many(key_list)
                    # response = DistributorOrderListGetSerializer(
                    #     queryset,
                    #     context={'request': self.request},
                    #     many=True
                    # )
                    response = {
                        'message': 'Success',
                        'orders': list(queryset.values_list('pk', flat=True))
                    }
                    return Response(
                        # response.data,
                        response,
                        status=status.HTTP_201_CREATED
                    )
                content = {'error': "Missing order ids"}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class OrderBulkStatusUpdate(APIView):

    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsDeliveryHub,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsSalesManager,
    )
    permission_classes = (CheckAnyPermission,)

    def post(self, request):
        is_distributor = self.request.user.profile_details.organization.type == OrganizationType.DISTRIBUTOR
        hours = self.request.data.get('hours', 48)
        current_order_status = self.request.data.get('current_order_status', OrderTrackingStatus.PENDING)
        tracking_status = dict(OrderTrackingStatus().choices())
        current_order_status_value = tracking_status.get(current_order_status)
        if hours:
            hours = int(hours)
        else:
            hours = 48

        if not is_distributor:
            content = {'error': "YOU DO NOT HAVE PERMISSION TO PERFORM THIS ACTION."}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        start_date_time = timezone.make_aware(datetime.now(), timezone.get_current_timezone()) - timedelta(hours = hours)
        end_date_time = timezone.make_aware(datetime.now(), timezone.get_current_timezone())

        filters = {
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER,
            "distributor": self.request.user.organization_id,
        }
        queryset = Purchase.objects.filter(**filters).only('id', 'current_order_status',)
        filter_params = {
            'date_0': start_date_time,
            'date_1': end_date_time,
            'current_order_status': current_order_status
        }
        queryset = DistributorOrderListFilter(request.data, queryset).qs
        order_id_list = list(queryset.values_list('pk', flat=True))
        # Rebuild ES doc
        chunk_size = 100
        total_order = len(order_id_list)
        index = 0

        while index < total_order:
            next_index = index + chunk_size
            custom_elastic_rebuild(
                'pharmacy.models.Purchase', {'id__in': order_id_list[index:next_index]})
            index = next_index

        # Apply bulk update
        queryset.update(
            current_order_status=OrderTrackingStatus.ACCEPTED,
            updated_by_id=self.request.user.id
        )

        for order_id in order_id_list:
            order_tracking_instance = OrderTracking.objects.create(
                order_id=order_id,
                entry_by_id=self.request.user.id,
                order_status=OrderTrackingStatus.ACCEPTED,
                remarks="Your order has been accepted."
            )

        if order_id_list:
            response_data = {
                "status": "Ok",
                "message": f"Total {len(order_id_list)} order status Changed from {current_order_status_value} to Accepted.",
            }
        else:
            response_data = {
                "status": "Ok",
                "message": "No {} order found for delivery date {}.".format(
                    current_order_status_value,
                    request.data.get('tentative_delivery_date_0', '')
                )
            }

        return Response(response_data, status=status.HTTP_200_OK)


class OrderClone(APIView):

    available_permission_classes = (
        IsSuperUser,
        StaffIsAdmin,
        StaffIsTelemarketer,
        StaffIsSalesCoordinator,
        StaffIsDeliveryHub,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsFrontDeskProductReturn,
        StaffIsSalesManager
    )
    permission_classes = (CheckAnyPermission,)

    def post(self, request):
        from expo_notification.tasks import send_push_notification_to_mobile_app
        try:
            order_alias =request.data.get('alias', '')
            order = Purchase.objects.get(alias=order_alias)
            if order.invoice_group_id:
                invoice_group_id = order.invoice_group_id
                response_data = {
                    "error": f"You can't clone this order as it has linked with a invoice group #{invoice_group_id}. Clone the invoice group instead."
                }
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

            new_order, order_group = order.clone_order()
            notification_title = "Order Update"
            notification_body = f"We are sorry for the failed delivery of #{order.id} instead we will deliver #{new_order.id}"
            notification_data = {
                "order_alias": str(new_order.alias),
                "order_group_alias": str(order_group.alias)
            }
            send_push_notification_to_mobile_app.delay(
                new_order.entry_by_id,
                title=notification_title,
                body=notification_body,
                data=notification_data,
                entry_by_id=request.user.id
            )
            response_data = {
                "status": "Ok",
                "message": f"Successfully cloned order #{order.id} as #{new_order.id}"
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class ProcessingToDeliverStockList(ListAPICustomView):
    """ Items those are ready to delivery """

    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
        StaffIsReceptionist,
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = ProcessingToDeliverStockListSerializer
    pagination_class = None

    def get_queryset(self):
        order_filters = {
            "purchase__status": Status.DISTRIBUTOR_ORDER,
            "purchase__distributor_order_type": DistributorOrderType.ORDER,
            "purchase__purchase_type": PurchaseType.VENDOR_ORDER,
            "purchase__current_order_status__in":[
                OrderTrackingStatus.PENDING,
                OrderTrackingStatus.ACCEPTED,
                OrderTrackingStatus.IN_QUEUE,
                OrderTrackingStatus.READY_TO_DELIVER,
                OrderTrackingStatus.ON_THE_WAY,
            ]
        }
        return StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization__id=self.request.user.organization_id,
            **order_filters
        ).only(
            "stock",
            "quantity",
        ).order_by()


class RequisitionRelatedPurchaseOrderProcurement(RetrieveAPIView):

    available_permission_classes = (
        StaffIsReceptionist,
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsSalesman,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = RequisitionRelatedPurchaseOrderProcurementSerializer
    pagination_class = CachedCountPageNumberPagination
    lookup_field = 'alias'

    def get_queryset(self):
        from procurement.models import Procure

        purchases = Purchase.objects.filter(
            status=Status.ACTIVE,
            purchase_type=PurchaseType.PURCHASE
        )

        orders = Purchase.objects.filter(
            status=Status.PURCHASE_ORDER,
            purchase_type=PurchaseType.ORDER
        ).prefetch_related(
            Prefetch(
                'purchases',
                queryset=purchases,
            ),
        )
        queryset = Purchase.objects.filter(
            purchase_type=PurchaseType.REQUISITION
        ).prefetch_related(
            Prefetch(
                'procure_requisitions',
                queryset=Procure().get_all_actives(),
                to_attr='procurements'
            ),
            Prefetch(
                'purchase_requisitions',
                queryset=orders,
                to_attr='orders'
            ),
        )
        return queryset


class CancelOrderFromCustomerEnd(RetrieveDestroyAPIView):
    available_permission_classes = (
        IsOwner,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)
    lookup_field = 'alias'

    def delete(self, request, *args, **kwargs):
        alias = kwargs.get('order_alias', None)
        try:
            order = Purchase.objects.filter(
                alias=alias,
            ).exclude(
                current_order_status=OrderTrackingStatus.CANCELLED
            ).values(
                'id',
                'alias',
                'status',
                'current_order_status',
                'is_queueing_order',
                'invoice_group',
                'purchase_date',
                'tentative_delivery_date',
            ).first()
            if order['invoice_group'] is not None:
                return Response(
                    {
                        'detail': _('THE_ORDER_IS_ALREADY_ON_THE_WAY_TO_DELIVER')
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                if order['current_order_status'] in [OrderTrackingStatus.PENDING, OrderTrackingStatus.IN_QUEUE, OrderTrackingStatus.ACCEPTED]:
                    Purchase.objects.filter(alias=alias).update(
                        current_order_status=OrderTrackingStatus.CANCELLED,
                    )
                    OrderTracking.objects.create(
                        order_id=order["id"],
                        entry_by_id=request.user.id,
                        order_status=OrderTrackingStatus.CANCELLED
                    )
                    custom_elastic_rebuild(
                        'pharmacy.models.Purchase',
                        {'id': order['id']}
                    )
                    key_list = [
                        'purchase_distributor_order_{}'.format(str(order['id']).zfill(12)),
                    ]
                    cache.delete_many(key_list)
                    return Response({'detail': _('ORDER_CANCELLED SUCCESSFULLY')}, status=status.HTTP_200_OK)
        except Exception as ObjectDoesNotExist:
            return Response({'detail': _('ORDER_NOT_FOUND')}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


class DistributorOrderRatings(CreateAPIView):
    from pharmacy.custom_serializer.purchase import DistributorOrderRatingSerializer
    serializer_class = DistributorOrderRatingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response("Rating Successfully Updated!", status=status.HTTP_200_OK)


class OrderPreOrderGraphList(ListAPICustomView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsSalesman,
        StaffIsAdmin,
        StaffIsTrader,
        StaffIsReceptionist,
        StaffIsTelemarketer,
        StaffIsMarketer,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = OrderPreOrderGraphListSerializer
    pagination_class = None

    def get_queryset(self):
        current_date_time = datetime.now()
        period = self.request.query_params.get("period", "")

        def generate_hour_range(start_date_hour, end_date_hour):
            initial_date_time = start_date_hour
            while initial_date_time < end_date_hour:
                yield initial_date_time
                initial_date_time += timedelta(hours=1)

        start_date = get_date_time_from_period(period)
        end_date = current_date_time

        filters = {
            "purchase_date__range": (start_date, end_date),
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER
        }

        all_hours = list(generate_hour_range(start_date, end_date))
        data = {hour.strftime('%Y-%m-%dT%H:%M:%S'): {"orders": 0, "pre_orders": 0} for hour in all_hours}

        query_sets = Purchase.objects.filter(
            **filters
        ).annotate(
            purchase_hour=TruncHour('purchase_date')
        ).values('purchase_hour').annotate(
            total_orders=Sum(Case(
                When(is_queueing_order=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )),
            total_preorder=Sum(Case(
                When(is_queueing_order=True, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            ))
        ).values('purchase_hour', 'total_orders', 'total_preorder')

        for queryset in query_sets:
            hour = queryset['purchase_hour'].strftime('%Y-%m-%dT%H:%M:%S')
            if hour in data:
                data[hour]['orders'] = queryset['total_orders']
                data[hour]['pre_orders'] = queryset['total_preorder']

        result_data = [
            {
                'orders': data[hour]['orders'],
                'pre_orders': data[hour]['pre_orders'],
                'date_time': hour
            }
            for hour in data
        ]

        return result_data