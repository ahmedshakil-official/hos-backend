import os

from datetime import datetime, timedelta, time, timezone as DTTZ
from django.core.cache import cache
from django.db.models import Prefetch, Q, Value, BooleanField
from django.db.models import Sum, F, Count, Case, When, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from core.helpers import get_user_profile_details_from_cache
from core.permissions import (
    CheckAnyPermission,
    StaffIsAdmin,
    StaffIsNurse,
    StaffIsProcurementOfficer,
    StaffIsSalesman,
    AnyLoggedInUser,
    StaffIsDistributionT1,
)
from core.views.common_view import ListAPICustomView
from core.enums import OrganizationType, AllowOrderFrom
from core.models import Organization

from common.utils import (
    filter_global_product_based_on_settings,
    generate_code_with_hex_of_organization_id,
    string_to_bool, convert_utc_to_local,
    get_healthos_settings,
)
from common.enums import Status
from common.helpers import pk_extractor, to_boolean
from common.healthos_helpers import HealthOSHelper
from common.healthos_helpers import CustomerHelper
from common.tasks import bulk_cache_write
from common.pagination import (
    FasterPageNumberPaginationWithDefaultCount,
    FasterPageNumberPagination,
)
from common.cache_keys import STOCK_INSTANCE_DISTRIBUTOR_CACHE_KEY_PREFIX
from pharmacy.models import Stock, StorePoint, StockIOLog
from pharmacy.custom_serializer.stock_product_service import (
    StockProductCachedListSerializer,
    StockProductNonCachedListSerializer,
)
from pharmacy.custom_serializer.stock import DistributorSalesableStock
from pharmacy.serializers import StockWithProductForRequisitionSerializer
from pharmacy.enums import StorePointType, DistributorOrderType, PurchaseType
from pharmacy.filters import DistributorSalesAbleStockProductListFilter
from pharmacy.utils import (
    get_sorting_options,
    get_sorting_value,
    get_delivery_date_for_product,
    get_organization_order_closing_and_reopening_time,
    remove_discount_factor_for_coupon,
    get_product_dynamic_discount_rate
)

class StockProductBaseView(object):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsSalesman,
        StaffIsNurse,
        StaffIsProcurementOfficer,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission, )
    lookup_field = 'alias'

    def query_by_keyword(self, queryset):
        """[filter queryset based on query string or bar code]
        Arguments:
            queryset {[object]} -- [description]
        Returns:
            [object] -- [queryset object]
        """
        keyword = self.request.GET.get('keyword', '')
        is_bar_code = self.request.GET.get('bar_code', None)
        # generate code for barcode
        generated_code = generate_code_with_hex_of_organization_id(
            self.request, keyword)

        # If barcode true then filter the product by code
        if is_bar_code:
            filter_queryset = queryset.filter(
                product__code__iexact=generated_code)
            if not filter_queryset and \
                    self.request.user.organization.show_global_product:
                generated_code = generate_code_with_hex_of_organization_id(
                    0, keyword)
                filter_queryset = queryset.filter(
                    product__code__iexact=generated_code)

            queryset = filter_queryset

        elif keyword:
            keyword = " ".join(keyword.split())
            keywords = keyword.split(" ")
            if len(keywords) == 1:
                queryset = queryset.filter(
                    product_full_name__contains=keyword.lower()
                )
            elif len(keywords) > 1:
                for each_keyword in keywords:
                    queryset = queryset.filter(
                        product_full_name__contains=each_keyword.lower()
                    )
        queryset = filter_global_product_based_on_settings(self, queryset)
        return queryset

    def get_from_db(self, list_of_pks=None, request=None, sales_able=True, is_distributor_stock=False):
        """[get_from_db]
        Arguments:
        list_of_pks {[list]} -- [List of PKs needs to fetch data from db]
        request {[obj]} -- [request object]
        """
        if not is_distributor_stock:
            queryset = StockProductNonCachedListSerializer.Meta.model().get_queryset_for_cache(
                list_of_pks, request=request)

            page = self.paginate_queryset(queryset)
            serializer = StockProductNonCachedListSerializer(
                'json', page, many=True, context={'sales_able': sales_able, 'request': request})
        else:
            queryset = DistributorSalesableStock.ListForSuperAdmin.Meta.model().get_queryset_for_cache(
                list_of_pks, request=request)

            page = self.paginate_queryset(queryset)
            serializer = DistributorSalesableStock.ListForSuperAdmin(
                'json', page, many=True, context={'request': request})
        serializer.is_valid()
        return self.get_paginated_response(serializer.data)

    def get_from_cache(
        self,
        page,
        request,
        cache_key=None,
        sales_able=True,
        is_distributor_stock=False):

        # page = self.paginate_queryset(queryset)
        response = []
        order_closing_date, order_reopening_date = get_organization_order_closing_and_reopening_time()
        is_order_enabled = not order_closing_date and not order_reopening_date
        # discount_rate_factor = CustomerHelper(
        #     request.user.organization_id
        # ).get_cumulative_discount_factor()
        # coupon = os.environ.get("EXPRESS_DELIVERY_STOCK_ID", None)

        if cache_key is None:
            # preparing key for retrival / set of cache
            module = self.get_serializer().__module__
            name = type(self.get_serializer()).__name__
            base_key = "{}.{}".format(module, name).replace(".", "_").lower()
        else:
            base_key = cache_key

        if page is not None:
            # finding every items pk
            objects_pk = pk_extractor(page)

            cache_key_list = ["{}_{}".format(base_key, str(
                item).zfill(12)) for item in objects_pk]

            cached_data = cache.get_many(cache_key_list)

            if len(cached_data) < 20:

                missing_key_data = []
                for index, item in enumerate(cache_key_list):
                    if item not in cached_data:
                        missing_key_data.append(objects_pk[index])
                if missing_key_data:
                    missing_data_queryset = \
                        self.get_serializer().Meta.model().get_queryset_for_cache(
                            missing_key_data,
                            request=request,
                            is_distributor_stock=is_distributor_stock
                        )

                    new_cached_data = {}
                    missing_serialized_data = self.get_serializer_class()(
                        missing_data_queryset,
                        many=True,
                        context={'request': request}
                    )
                    for missing_item in missing_serialized_data.data:
                        data = dict(missing_item)
                        stock_id = data.get("id")
                        missing_key = f"{base_key}_{str(stock_id).zfill(12)}"
                        new_cached_data.update({missing_key: missing_item})

                    # for each_missing_item in missing_data_queryset:
                    #     missing_key = "{}_{}".format(
                    #         base_key, str(each_missing_item.id).zfill(12))
                    #     serializer = self.get_serializer_class()(
                    #         'json',
                    #         [each_missing_item],
                    #         many=True,
                    #         context={'request': request}
                    #     )
                    #     serializer.is_valid()
                    #     new_cached_data.update({missing_key: serializer.data[0]})

                    bulk_cache_write.apply_async(
                        (new_cached_data,),
                        countdown=5,
                        retry=True, retry_policy={
                            'max_retries': 10,
                            'interval_start': 0,
                            'interval_step': 0.2,
                            'interval_max': 0.2,
                        }
                    )

                    cached_data.update(new_cached_data)
            # for index, item in enumerate(objects_pk):
            #     key = "{}_{}".format(base_key, str(item).zfill(12))
            #     # inject log_price based on sales and purchase
            #     if not is_distributor_stock:
            #         log_price = cached_data[key]['log_price']
            #         if sales_able:
            #             cached_data[key]['log_price'] = cached_data[key].get(
            #                 'sales_log_price', log_price)
            #         else:
            #             cached_data[key]['log_price'] = cached_data[key].get(
            #                 'purchase_log_price', log_price)
            #     elif is_distributor_stock and not request.user.is_superuser:
            #         cached_data[key].pop('avg_purchase_rate_days', '')
            #     response.append(cached_data[key])
            # Perform log_price and avg_purchase_rate related operations
            if not is_distributor_stock and sales_able:
                for index, item in enumerate(objects_pk):
                    key = "{}_{}".format(base_key, str(item).zfill(12))
                    try:
                        is_queueing_item = cached_data[key]['product']['is_queueing_item']
                    except:
                        is_queueing_item = True
                    cached_data[key]['delivery_date'] = get_delivery_date_for_product(
                        is_queueing_item
                    )
                    cached_data[key]['is_order_enabled'] = is_order_enabled
                    log_price = cached_data[key]['log_price']
                    # Inject log_price for sales
                    cached_data[key]['log_price'] = cached_data[key].get(
                        'sales_log_price', log_price)

                    cached_data[key]["product"]['discount_rate_factor'] = remove_discount_factor_for_coupon(
                        request = request,
                        data = cached_data[key]
                    )
                    cached_data[key]["product"]["dynamic_discount_rate"] = get_product_dynamic_discount_rate(
                        user_org_id=request.user.organization_id,
                        stock_id=cached_data[key]["id"],
                        trading_price=cached_data[key]["product"]["trading_price"],
                        discount_rate=cached_data[key]["product"]["discount_rate"]
                    )
                    cached_data[key]["product"]["dynamic_discount_factors"] = CustomerHelper(
                        organization_id=request.user.organization_id
                    ).get_organization_and_area_discount()

                    response.append(cached_data[key])
            elif not is_distributor_stock and not sales_able:
                for index, item in enumerate(objects_pk):
                    key = "{}_{}".format(base_key, str(item).zfill(12))
                    try:
                        is_queueing_item = cached_data[key]['product']['is_queueing_item']
                    except:
                        is_queueing_item = True

                    cached_data[key]['delivery_date'] = get_delivery_date_for_product(
                        is_queueing_item
                    )
                    cached_data[key]['is_order_enabled'] = is_order_enabled
                    log_price = cached_data[key]['log_price']
                    # Inject log_price for Purchase / Order
                    cached_data[key]['log_price'] = cached_data[key].get(
                        'purchase_log_price', log_price)

                    cached_data[key]["product"]['discount_rate_factor'] = remove_discount_factor_for_coupon(
                        request = request,
                        data = cached_data[key]
                    )
                    cached_data[key]["product"]["dynamic_discount_rate"] = get_product_dynamic_discount_rate(
                        user_org_id=request.user.organization_id,
                        stock_id=cached_data[key]["id"],
                        trading_price=cached_data[key]["product"]["trading_price"],
                        discount_rate=cached_data[key]["product"]["discount_rate"]
                    )
                    cached_data[key]["product"]["dynamic_discount_factors"] = CustomerHelper(
                        organization_id=request.user.organization_id
                    ).get_organization_and_area_discount()

                    response.append(cached_data[key])
            # elif is_distributor_stock and not request.user.is_superuser:
            #     for index, item in enumerate(objects_pk):
            #         key = "{}_{}".format(base_key, str(item).zfill(12))
            #         # Remove avg_purchase_rate_days data for non su admin
            #         cached_data[key].pop('avg_purchase_rate_days', '')
            #         response.append(cached_data[key])
            else:
                for index, item in enumerate(objects_pk):
                    key = "{}_{}".format(base_key, str(item).zfill(12))
                    try:
                        is_queueing_item = cached_data[key]['product']['is_queueing_item']
                    except:
                        is_queueing_item = True
                    cached_data[key]['delivery_date'] = get_delivery_date_for_product(
                        is_queueing_item
                    )
                    cached_data[key]['is_order_enabled'] = is_order_enabled

                    cached_data[key]["product"]['discount_rate_factor'] = remove_discount_factor_for_coupon(
                        request = request,
                        data = cached_data[key]
                    )
                    cached_data[key]["product"]["dynamic_discount_rate"] = get_product_dynamic_discount_rate(
                        user_org_id=request.user.organization_id,
                        stock_id=cached_data[key]["id"],
                        trading_price=cached_data[key]["product"]["trading_price"],
                        discount_rate=cached_data[key]["product"]["discount_rate"]
                    )
                    cached_data[key]["product"]["dynamic_discount_factors"] = CustomerHelper(
                        organization_id=request.user.organization_id
                    ).get_organization_and_area_discount()

                    response.append(cached_data[key])

        return self.get_paginated_response(response)

    def get_ordered_queryset(self, queryset):
        """[apply order_by in queryset based on different case]
        Arguments:
            queryset {[object]} -- [description]
        Returns:
            [object] -- [ordered queryset]
        """
        keyword = self.request.GET.get('keyword', '')
        # check any letter in keyword is in uppercase
        is_exact_search = True if any(
            map(str.isupper, str(keyword))) else False

        if is_exact_search:
            queryset = queryset.order_by(
                'product_len',
                # '-local_count',
                # '-organizationwise_count',
                # '-global_count',
                'product_full_name'
            )

        elif keyword:
            queryset = queryset.order_by(
                # '-local_count',
                # '-organizationwise_count',
                # '-global_count',
                'product_len',
                'product_full_name'
            )

        else:
            queryset = queryset.order_by(
                # '-local_count',
                # '-organizationwise_count',
                # '-global_count',
                'product_full_name'
            )
        return queryset

    def get_order_by_fields(self, pre=[], post=[]):
        """[create order_by tuple based on different case]
        Returns:
            [list] -- [order by fields]
        """
        keyword = self.request.GET.get('keyword', '')
        # check any letter in keyword is in uppercase
        is_exact_search = True if any(
            map(str.isupper, str(keyword))) else False
        order = pre if pre else []

        if is_exact_search:
            order += [
                'product_len',
                # '-local_count',
                # '-organizationwise_count',
                # '-global_count',
                'product_full_name'
            ]

        elif keyword:
            order += [
                # '-local_count',
                # '-organizationwise_count',
                # '-global_count',
                'product_len',
                'product_full_name'
            ]

        else:
            order += [
                # '-local_count',
                # '-organizationwise_count',
                # '-global_count',
                'product_full_name'
            ]
        return order + post if post else order

    def get_prepared_list(self, sales_able=True, cache_key='stock_instance', is_distributor_stock=False):
        """[return paginated queryset]
        Keyword Arguments:
            sales_able {bool} -- [description] (default: {True})
        Returns:
            [response] -- [paginated response data]
        """
        queryset = self.get_queryset().values_list('id', flat=True)
        # when cache is false get data from database otherwise from cache
        from_cache = self.request.GET.get('cache', None)
        page = self.paginate_queryset(queryset)

        if page:
            if from_cache and from_cache == "false":
                return self.get_from_db(
                    list_of_pks=list(queryset),
                    request=self.request,
                    sales_able=sales_able,
                    is_distributor_stock=is_distributor_stock
                )
            return self.get_from_cache(
                page=page,
                request=self.request,
                cache_key=cache_key,
                sales_able=sales_able,
                is_distributor_stock=is_distributor_stock
            )
        page = self.paginate_queryset([])
        return self.get_paginated_response([])


class SalesAbleStockProductCachedList(ListAPICustomView, StockProductBaseView):
    serializer_class = StockProductCachedListSerializer
    pagination_class = FasterPageNumberPaginationWithDefaultCount

    def get_queryset(self):
        store_point_alias = self.kwargs['alias']
        product = self.request.GET.get('product', None)
        purchases = self.request.GET.get('purchases', None)
        buyer = self.request.GET.get('person', None)

        try:
            store_point = StorePoint.objects.only(
                'id', 'auto_adjustment').get(alias=store_point_alias)
        except StorePoint.DoesNotExist:
            store_point = None

        organization_settings = self.request.user.organization.get_settings()

        # If auto adjustment is disabled for organization then fetch stocks amount greater than zero
        minimum_stock = 0

        # minimum stock -1 when organization auto adjustment true
        # store point auto adjustment disable then fetch stocks amount greater than zero
        if store_point and minimum_stock == -1 and not store_point.auto_adjustment:
            minimum_stock = 0

        # skiped_products = self.request.user.organization.get_discarded_product()
        # add organization wise allowed negative stock

        queryset = Stock.objects.filter(
            organization=self.request.user.organization_id,
            status=Status.ACTIVE,
            is_salesable=True,
            is_service=False,
            store_point=store_point,
            stock__gt=minimum_stock
        ).only(
            # 'id',
            # 'stock',
            # 'minimum_stock',
            # 'product__status',
            # 'product__is_salesable',
            # 'product__is_printable',
            # 'product__is_service',
            # 'product__is_global',
        )

        queryset = self.query_by_keyword(queryset)

        if product:
            queryset = queryset.filter(
                product__alias=product
            )

        if purchases:
            queryset = queryset.filter(
                stocks_io__purchase__in=purchases.split(',')
            ).order_by('product').distinct()

        if buyer:
            queryset = queryset.filter(
                stocks_io__sales__person_organization_buyer__alias=buyer
            ).order_by('product').distinct()

        # queryset = add_log_price_on_stock_queryset(queryset)

        return self.get_ordered_queryset(queryset)

    def list(self, request, *args, **kwargs):
        return self.get_prepared_list()


class StockProductCachedList(ListAPIView, StockProductBaseView):

    requisition = transfer_requisition = order = purchase = None
    pagination_class = FasterPageNumberPaginationWithDefaultCount

    def initialize_params(self):
        # set params values
        self.requisition = self.request.GET.get('requisition', None)
        self.transfer_requisition = self.request.GET.get('transfer_requisition', None)
        self.order = self.request.GET.get('order', None)
        self.purchase = self.request.GET.get('purchase', None)

    def get_serializer_class(self):
        if self.requisition or self.order or self.purchase or self.transfer_requisition:
            return StockWithProductForRequisitionSerializer
        return StockProductCachedListSerializer

    def heavy_queryset(self, queryset):
        store_point_alias = self.kwargs['alias']
        if self.requisition:
            stocks_io = StockIOLog.objects.filter(
                organization=self.request.user.organization_id,
                status=Status.DRAFT,
                stock__store_point__alias=store_point_alias,
                purchase__alias=self.requisition
            )
            queryset = queryset.prefetch_related(
                Prefetch('stocks_io', queryset=stocks_io)
            ).filter(
                stocks_io__purchase__alias=self.requisition
            ).order_by('product').distinct()

        if self.order:
            stocks_io = StockIOLog.objects.filter(
                organization=self.request.user.organization_id,
                status=Status.PURCHASE_ORDER,
                stock__store_point__alias=store_point_alias,
                purchase__alias=self.order
            )
            queryset = queryset.prefetch_related(
                Prefetch('stocks_io', queryset=stocks_io)
            ).filter(
                stocks_io__purchase__alias=self.order
            ).order_by('product').distinct()

        if self.purchase:
            stocks_io = StockIOLog.objects.filter(
                organization=self.request.user.organization_id,
                status=Status.ACTIVE,
                stock__store_point__alias=store_point_alias,
                purchase__alias=self.purchase
            )
            queryset = queryset.prefetch_related(
                Prefetch('stocks_io', queryset=stocks_io)
            ).filter(
                stocks_io__purchase__alias=self.purchase
            ).order_by('product').distinct()

        if self.transfer_requisition:
            stocks_io = StockIOLog.objects.filter(
                organization=self.request.user.organization_id,
                status=Status.DRAFT,
                stock__store_point__alias=store_point_alias,
                transfer__alias=self.transfer_requisition
            )
            queryset = queryset.prefetch_related(
                Prefetch('stocks_io', queryset=stocks_io)
            ).filter(
                stocks_io__transfer__alias=self.transfer_requisition
            ).order_by('product').distinct()
        return queryset

    def get_queryset(self):
        store_point_alias = self.kwargs['alias']
        keyword = self.request.GET.get('keyword', '')
        second_store_point = self.request.GET.get(
            'second_store_point', None)
        manufacturing_company = self.request.GET.get(
            'manufacturing_company', None)
        form = self.request.GET.getlist('form')
        is_service = self.request.GET.get('is_service', None)
        is_salesable = to_boolean(self.request.GET.get('is_service', None))
        product_alias = self.request.GET.get('product', None)
        supplier = self.request.GET.get('person', None)
        exact_search = self.request.GET.get('exact_search', None)
        sales_list = self.request.GET.get('sales_list', None)

        # if requisition or order or purchase or transfer_requisition:
        #     self.pagination_class = None

        is_stock_out = self.request.GET.get('is_stock_out', None)
        # If auto adjustment is disabled for organization then
        # fetch stocks amount greater than zero
        # is stock out true when request from stock transfer or disbursement
        # and organization auto adjustment disable
        minimum_stock = -1
        if not is_stock_out:
            minimum_stock = 0

        try:
            store_point = StorePoint.objects.only(
                'id', 'auto_adjustment').get(alias=store_point_alias)
        except StorePoint.DoesNotExist:
            store_point = None

        # minimum stock -1 when organization auto adjustment true
        # store point auto adjustment disable then fetch stocks amount greater than zero
        if store_point and is_stock_out and minimum_stock == -1 and \
                not store_point.auto_adjustment:
            minimum_stock = 0

        queryset = Stock.objects.filter(
            organization=self.request.user.organization_id,
            status=Status.ACTIVE,
            stock__gt=minimum_stock,
            store_point=store_point,
        )

        queryset = self.query_by_keyword(queryset)

        if second_store_point:
            second_store_point_queryset = Stock.objects.filter(
                organization=self.request.user.organization_id,
                status=Status.ACTIVE,
                product_full_name__contains=keyword.lower(),
                store_point__alias__in=second_store_point.split(','),
            ).values_list('product', flat=True)
            queryset = queryset.filter(
                product__in=second_store_point_queryset)

        if product_alias:
            queryset = queryset.filter(product__alias=product_alias)

        if supplier:
            queryset = queryset.filter(
                stocks_io__purchase__person_organization_supplier__alias=supplier
            ).order_by('product').distinct()

        if is_service in ['True', 'False']:
            queryset = queryset.filter(product__is_service=is_service)

        if is_salesable:
            queryset = queryset.filter(product__is_salesable=is_salesable)

        if manufacturing_company:
            queryset = queryset.filter(
                product__manufacturing_company__alias=manufacturing_company)

        if form:
            queryset = queryset.filter(product__form__alias__in=form)

        if exact_search:
            queryset = queryset.filter(product__name__istartswith=exact_search)

        if sales_list:
            sales_list = [int(sale) for sale in sales_list.split(',')]
            queryset = queryset.filter(
                stocks_io__sales__in=sales_list).distinct()

        # queryset = add_log_price_on_stock_queryset(queryset, False)
        return self.get_ordered_queryset(queryset)

    def list(self, request, *args, **kwargs):
        self.initialize_params()
        # process heavy query if requisitions or other related params available
        if self.requisition or self.order or self.purchase or self. transfer_requisition:
            serializer = self.get_serializer(
                self.heavy_queryset(self.get_queryset()),
                many=True
            )
            return Response(serializer.data)
        return self.get_prepared_list(False)


class DistributorSalesAbleStockProductList(ListAPICustomView, StockProductBaseView):

    filterset_class = DistributorSalesAbleStockProductListFilter
    pagination_class = FasterPageNumberPaginationWithDefaultCount

    # def get_serializer_class(self):
    #     if not self.request.user.is_superuser:
    #         return DistributorSalesableStock.ListForGeneralUser
    #     return DistributorSalesableStock.ListForSuperAdmin
    serializer_class = DistributorSalesableStock.ListForSuperAdmin

    def get_queryset(self):

        healthos_settings = get_healthos_settings()

        keyword = self.request.GET.get('keyword', '')
        starts_with = self.request.GET.get('starts_with', '')
        is_recent_orders = string_to_bool(
            self.request.GET.get('recent_orders', None))
        trending_products = string_to_bool(
            self.request.GET.get('trending_products', None)
        )
        flash_products = string_to_bool(
            self.request.GET.get('flash_products', None)
        )
        sort_by = self.request.GET.get('sort_by', 'name_a_to_z')
        sort_by = [str(get_sorting_value(sort_by))]

        queryset = Stock.objects.filter(
            status=Status.ACTIVE,
            organization__type=OrganizationType.DISTRIBUTOR,
            store_point__type=StorePointType.VENDOR_DEFAULT,
            product__is_published=True,
            product__order_limit_per_day__gt=0,
            is_salesable=True,
            # is_service=False,
        )

        if "price_low_to_high" or "price_high_to_low" in self.request.GET.get("sort_by", ""):
            queryset = queryset.annotate(
                product_discounted_price=F("product__trading_price") - (F("product__trading_price") * F("product__discount_rate")) / 100
            )

        if healthos_settings.allow_order_from == AllowOrderFrom.STOCK and not healthos_settings.overwrite_order_mode_by_product:
            queryset = queryset.exclude(product__is_queueing_item=True)
        elif healthos_settings.overwrite_order_mode_by_product:
            queryset = queryset.exclude(
                product__is_queueing_item=True,
                product__order_mode=AllowOrderFrom.STOCK
            )

        if is_recent_orders:
            queryset = queryset.filter(
                pk__in=self.request.user.get_stocks_from_recent_orders()
            )

        if flash_products:
            queryset = queryset.filter(
                product__is_flash_item=True
            )

        if keyword:
            keyword = " ".join(keyword.split())
            keywords = keyword.split(" ")
            # with product_full_name it can be product__manufacturing_company__name too
            filters = Q(
                product__full_name__icontains=keyword.lower()
            ) | Q(
                product__generic__name__icontains=keyword.lower()
            ) | Q(
                product__manufacturing_company__name__icontains=keyword.lower()
            )
            if len(keywords) == 1:
                queryset = queryset.filter(
                    filters
                )
            elif len(keywords) > 1:
                for each_keyword in keywords:
                    queryset = queryset.filter(
                        filters
                    )
        elif starts_with:
            queryset = queryset.filter(product_full_name__startswith=starts_with.lower())

        queryset = self.filterset_class(self.request.GET, queryset).qs
        if trending_products:
            hours = 24
            start_date_time = timezone.make_aware(
                datetime.now(), timezone.get_current_timezone()
            ) - timedelta(hours = hours)
            end_date_time = timezone.make_aware(datetime.now(), timezone.get_current_timezone())
            trending_items_pk_list = list(StockIOLog.objects.filter(
                status=Status.DISTRIBUTOR_ORDER,
                purchase__status=Status.DISTRIBUTOR_ORDER,
                purchase__distributor_order_type=DistributorOrderType.ORDER,
                purchase__purchase_type=PurchaseType.VENDOR_ORDER,
                purchase__purchase_date__range=[start_date_time, end_date_time]
            ).values_list('stock_id', flat=True).annotate(
                unique_pharmacy_order_count=Count('organization_id', distinct=True),
            ).order_by('-unique_pharmacy_order_count'))[:50]
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(trending_items_pk_list)])
            return queryset.filter(
                pk__in=trending_items_pk_list
            ).order_by(preserved)

        return queryset.order_by(*self.get_order_by_fields(sort_by))

    def list(self, request, *args, **kwargs):
        return self.get_prepared_list(
            sales_able=False, cache_key=STOCK_INSTANCE_DISTRIBUTOR_CACHE_KEY_PREFIX, is_distributor_stock=True)


class DistributorSalesAbleStockProductListV2(ListAPICustomView, StockProductBaseView):
    filterset_class = DistributorSalesAbleStockProductListFilter
    serializer_class = DistributorSalesableStock.ListForSuperAdmin
    pagination_class = FasterPageNumberPaginationWithDefaultCount

    def get_queryset(self):
        # try:
        #     healthos_settings = Organization.objects.only('id').get(pk=303).get_settings()
        # except Organization.DoesNotExist:
        #     healthos_settings = Organization.objects.only('id').get(pk=41).get_settings()
        healthos_settings = get_healthos_settings()
        user_details = get_user_profile_details_from_cache(self.request.user.id)
        keyword = self.request.GET.get('keyword', '')
        starts_with = self.request.GET.get('starts_with', '')
        manufacturing_company = self.request.GET.get('manufacturing_company', '')
        unit_type = self.request.GET.get('unit_type', '')
        generic = self.request.GET.get('generic', '')
        stock_aliases = self.request.GET.get("aliases", None)

        is_recent_orders = string_to_bool(
            self.request.GET.get('recent_orders', None))
        trending_products = string_to_bool(
            self.request.GET.get('trending_products', None)
        )
        flash_products = string_to_bool(
            self.request.GET.get('flash_products', None)
        )
        product_availability = self.request.GET.get('availability', '')
        sort_by = self.request.GET.get('sort_by', 'name_a_to_z')
        sort_by = [str(get_sorting_value(sort_by))]

        queryset = Stock.objects.filter(
            status=Status.ACTIVE,
            organization__type=OrganizationType.DISTRIBUTOR,
            store_point__type=StorePointType.VENDOR_DEFAULT,
            product__is_published=True,
        )
        if stock_aliases:
            queryset = queryset.filter(
                alias__in=stock_aliases.split(","),
            )
        # filter product order limit value based on delivery hub short_code
        try:
            short_code = user_details.organization.delivery_hub.short_code
            if short_code == "MH-1":
                queryset = queryset.filter(
                    product__order_limit_per_day_mirpur__gt=0
                )
            elif short_code == "UH-1":
                queryset = queryset.filter(
                    product__order_limit_per_day_uttara__gt=0
                )
            else:
                queryset = queryset.filter(
                    product__order_limit_per_day__gt=0
                )
        except:
            queryset = queryset.filter(
                product__order_limit_per_day__gt=0
            )

        if "price_low_to_high" or "price_high_to_low" in self.request.GET.get("sort_by", ""):
            queryset = queryset.annotate(
                product_discounted_price=F("product__trading_price") - (F("product__trading_price") * F("product__discount_rate")) / 100
            )

        if healthos_settings.allow_order_from == AllowOrderFrom.STOCK and not healthos_settings.overwrite_order_mode_by_product:
            queryset = queryset.exclude(product__is_queueing_item=True)
        # elif healthos_settings.allow_order_from == AllowOrderFrom.STOCK_AND_OPEN and not healthos_settings.overwrite_order_mode_by_product:
        #     queryset = queryset.exclude(
        #         product__is_queueing_item=True
        #         ).filter(
        #             Q(product__order_mode=AllowOrderFrom.STOCK) |
        #             Q(product__order_mode=AllowOrderFrom.OPEN) |
        #             Q(orderable_stock__gt=0)
        #     )
        elif healthos_settings.overwrite_order_mode_by_product:
            queryset = queryset.exclude(
                product__is_queueing_item=True,
                product__order_mode=AllowOrderFrom.STOCK
            )
        # Show out of stock products when keyword is given
        if keyword == "" and starts_with == "" and not is_recent_orders and not trending_products and not flash_products and manufacturing_company == "" and unit_type == "" and generic == "" and product_availability == "":
            queryset = queryset.filter(
                product__is_salesable=True
            )

        if is_recent_orders:
            queryset = queryset.filter(
                pk__in=self.request.user.get_stocks_from_recent_orders()
            )

        if flash_products:
            queryset = queryset.filter(
                product__is_flash_item=True
            )

        if keyword:
            keyword = " ".join(keyword.split())
            keywords = keyword.split(" ")
            # with product_full_name it can be product__manufacturing_company__name too
            filters = Q(
                product__full_name__icontains=keyword.lower()
            ) | Q(
                product__generic__name__icontains=keyword.lower()
            ) | Q(
                product__manufacturing_company__name__icontains=keyword.lower()
            )
            if len(keywords) == 1:
                queryset = queryset.filter(
                    filters
                )
            elif len(keywords) > 1:
                for each_keyword in keywords:
                    # queryset = queryset.filter(
                    #     filters
                    # )
                    queryset = queryset.filter(
                        Q(product__full_name__icontains=each_keyword.lower()) |
                        Q(product__generic__name__icontains=each_keyword.lower()) |
                        Q(product__manufacturing_company__name__icontains=each_keyword.lower())
                    )
        elif starts_with:
            queryset = queryset.filter(product_full_name__startswith=starts_with.lower())

        queryset = self.filterset_class(self.request.GET, queryset).qs
        healthos_helper = HealthOSHelper()
        if trending_products:
            requested_sorting = self.request.GET.get("sort_by", "")
            trending_items_pk_list = healthos_helper.get_trending_products_pk_list()
            if requested_sorting:
                return queryset.filter(
                    pk__in=trending_items_pk_list
                ).order_by(*self.get_order_by_fields(sort_by))
            else:
                preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(trending_items_pk_list)])
                return queryset.filter(
                    pk__in=trending_items_pk_list
                ).order_by(preserved)
        return queryset.order_by(*self.get_order_by_fields(sort_by))

    def list(self, request, *args, **kwargs):
        return self.get_prepared_list(
            sales_able=False, cache_key=STOCK_INSTANCE_DISTRIBUTOR_CACHE_KEY_PREFIX, is_distributor_stock=True)


class DistributorSalesAbleStockFlashProductList(DistributorSalesAbleStockProductList):

    def get_queryset(self):
        self.request.GET = self.request.GET.copy()
        self.request.GET['flash_products'] = 'true'
        self.request.GET['trending_products'] = 'false'
        self.request.GET['recent_orders'] = 'false'
        return super().get_queryset()


class DistributorSalesAbleStockTrendingProductList(DistributorSalesAbleStockProductListV2):

    def get_queryset(self):
        self.request.GET = self.request.GET.copy()
        self.request.GET['flash_products'] = 'false'
        self.request.GET['trending_products'] = 'true'
        self.request.GET['recent_orders'] = 'false'
        return super().get_queryset()


class DistributorSalesAbleStockRecentOrderedProductList(DistributorSalesAbleStockProductList):

    def get_queryset(self):
        self.request.GET = self.request.GET.copy()
        self.request.GET['flash_products'] = 'false'
        self.request.GET['trending_products'] = 'false'
        self.request.GET['recent_orders'] = 'true'
        return super().get_queryset()


class DistributorSalesAbleStockLatestProductListV2(DistributorSalesAbleStockProductListV2):

    def get_queryset(self):
        today = timezone.now().date()
        end_of_today = timezone.make_aware(datetime.combine(today, time(23, 59, 59)), DTTZ.utc)
        seven_days_ago = today - timedelta(days=7)
        queryset = super().get_queryset().order_by("-product__pk")

        latest_products = queryset.filter(
            last_publish__range=(
                timezone.make_aware(datetime.combine(seven_days_ago, time()), DTTZ.utc),
                end_of_today
            )
        )
        if latest_products.count() < 5:
            one_month_ago = today - timedelta(days=30)
            latest_products = queryset.filter(
                last_publish__range=(
                    timezone.make_aware(datetime.combine(one_month_ago, time()), DTTZ.utc),
                    end_of_today
                )
            )
        return latest_products


class DistributorSalesAbleStockRecentOrderedProductListV2(DistributorSalesAbleStockProductListV2):

    def get_queryset(self):
        self.request.GET = self.request.GET.copy()
        self.request.GET['flash_products'] = 'false'
        self.request.GET['trending_products'] = 'false'
        self.request.GET['recent_orders'] = 'true'
        return super().get_queryset()


class DistributorSalesAbleStockBestDiscountProductListV2(DistributorSalesAbleStockProductListV2):
    """
        A view for listing distributor sales-able stock products with the best discounts.

        This view extends the DistributorSalesAbleStockProductListV2 view and filters the products to display only those
        from the top 30 manufacturing companies with the highest discounts.

        Methods:
            get_queryset(self): Overrides the base class's get_queryset method to apply the filter for the best discounts.
    """
    def get_queryset(self):
        self.request.GET = self.request.GET.copy()
        self.request.GET["sort_by"] = "discount_high_to_low"

        # Create an object of the HealthOSHelper class
        healthos_helper = HealthOSHelper()

        # Get a list of the top sold stocks' primary key (PK) IDs
        top_sold_stocks_ids = healthos_helper.get_top_sold_stocks_pk_list()

        # Get the queryset using the parent class's get_queryset() method and
        # filter it to include only records with IDs in top_sold_stocks_ids
        queryset = super().get_queryset().filter(
            id__in=top_sold_stocks_ids
        )

        return queryset


class DistributorSalesAbleStockSimilarProductList(DistributorSalesAbleStockProductList):

    def get_queryset(self):
        queryset = super().get_queryset()
        stock_alias = self.kwargs.get('alias')
        stock = Stock.objects.values(
            'product__generic_id',
            'product__subgroup_id',
            'product__subgroup__product_group_id'
        ).get(alias=stock_alias)

        generic_id = stock.get("product__generic_id", None)
        subgroup_id = stock.get("product__subgroup_id", None)
        group_id = stock.get("product__subgroup__product_group_id", None)

        additional_sorting_for_ad = ["-is_ad_enabled", "-priority"]

        # Create an object of the HealthOSHelper class
        healthos_helper = HealthOSHelper()

        # Get a list of product generic IDs with null or "N/A" names
        null_name_product_generic_ids = healthos_helper.get_null_name_product_generic_pk_list()

        # Check if the generic ID is in the list of null or "N/A" names
        if generic_id not in null_name_product_generic_ids:
            # If not, filter the queryset based on the generic ID of the stock product
            # Exclude the stock with the provided alias
            queryset = queryset.filter(
                product__generic_id=generic_id
            ).exclude(
                alias=stock_alias
            ).values_list('pk', flat=True).order_by(*self.get_order_by_fields(additional_sorting_for_ad))

        else:
            # If yes, filter the queryset based on the subgroup ID of the stock product
            # Exclude the stock with the provided alias
            queryset = queryset.filter(
                product__subgroup_id=subgroup_id
            ).exclude(
                alias=stock_alias
            ).values_list('pk', flat=True).order_by(*self.get_order_by_fields(additional_sorting_for_ad))

        # Check if the count is less than 5
        if queryset.count() < 5:
            # If yes, filter the queryset based on the product group ID of the stock product
            # Exclude the stock with the provided alias
            queryset = queryset.filter(
                Q(product__subgroup__product_group_id=group_id) | Q(product__subgroup__product_group_id=group_id)
            ).exclude(
                alias=stock_alias
            ).values_list('pk', flat=True).order_by(*self.get_order_by_fields(additional_sorting_for_ad))

        return queryset


class DistributorSalesAbleStockRecommendedProductList(DistributorSalesAbleStockProductList):

    def get_queryset(self):
        max_items = 20
        queryset = super().get_queryset()
        filters = {
            "purchase__status": Status.DISTRIBUTOR_ORDER,
            "purchase__distributor_order_type": DistributorOrderType.ORDER,
            "purchase__purchase_type": PurchaseType.VENDOR_ORDER
        }
        stock_alias = self.kwargs.get('alias')
        stock = Stock.objects.only('product__generic_id').get(alias=stock_alias)

        related_orders = stock.stocks_io.filter(
            **filters,
            organization_id=self.request.user.organization_id,
        ).values_list('purchase_id', flat=True)[:max_items]

        if not related_orders.exists():
            related_orders = stock.stocks_io.filter(
                **filters,
            ).values_list('purchase_id', flat=True)[:max_items]

        recommended_stocks = StockIOLog.objects.filter(
            purchase__id__in=Subquery(related_orders)
        ).exclude(
            stock__alias=stock_alias
        ).order_by().values('stock_id').annotate(
            total_qty=Sum('quantity')
        ).order_by('-total_qty').values_list('stock_id', flat=True)[:max_items]

        recommended_stock_ids = list(recommended_stocks)

        if not recommended_stock_ids:
            related_orders = stock.stocks_io.filter(
                **filters,
            ).values_list('purchase_id', flat=True)[:max_items]

            recommended_stocks = StockIOLog.objects.filter(
                purchase__id__in=Subquery(related_orders)
            ).exclude(
                stock__alias=stock_alias
            ).order_by().values('stock_id').annotate(
                total_qty=Sum('quantity')
            ).order_by('-total_qty').values_list('stock_id', flat=True)[:max_items]
            recommended_stock_ids = list(recommended_stocks)

        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(recommended_stock_ids)])
        return queryset.filter(pk__in=recommended_stock_ids).order_by(preserved)


class DistributorStockDetails(RetrieveAPIView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsSalesman,
        StaffIsNurse,
        StaffIsProcurementOfficer,
    )

    permission_classes = (CheckAnyPermission, )
    serializer_class = DistributorSalesableStock.Details

    lookup_field = "alias"
    queryset = Stock().get_all_actives().select_related(
        "organization",
        "product__primary_unit",
        "product__secondary_unit",
    )

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve and return an object instance.
        Add a dynamic 'discount_rate_factor' to the response data.
        """
        # Retrieve the object instance
        instance = self.get_object()
        # Serialize the instance data
        serializer = self.get_serializer(instance)
        data = serializer.data
        # if stock is coupon then discount rate factor is 0.00
        data["product"]["discount_rate_factor"] = remove_discount_factor_for_coupon(
            request = request,
            data = data
        )
        data["product"]["dynamic_discount_rate"]= get_product_dynamic_discount_rate(
            user_org_id=request.user.organization_id,
            stock_id=data["id"],
            trading_price=data["product"]["trading_price"],
            discount_rate=data["product"]["discount_rate"]
        )
        data["product"]["dynamic_discount_factors"] = CustomerHelper(
            organization_id=request.user.organization_id
        ).get_organization_and_area_discount()
        return Response(data)



class StockChangeHistory(APIView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsSalesman,
        StaffIsNurse,
        StaffIsProcurementOfficer,
    )

    permission_classes = (CheckAnyPermission, )

    def get(self, request, alias):
        try:
            product_alias = alias
            stock_instance = Stock.objects.only(
                'ecom_stock',
            ).get(
                store_point__id=408,
                product__alias=product_alias
            )
            data = stock_instance.get_stock_change_history()
            return Response(data, status=status.HTTP_200_OK)

        except Exception as exception:
            exception_str = exception.args[0] if exception.args else str(exception)
            content = {'error': '{}'.format(exception_str)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class GetProductSortingOptions(APIView):
    available_permission_classes = (
        AnyLoggedInUser,
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        sorting_options = get_sorting_options()
        exclude_option_names = ["mrp_low_to_high", "mrp_high_to_low"]
        filtered_sorting_options = [option for option in sorting_options if option not in exclude_option_names]
        return Response(
            filtered_sorting_options,
            status=status.HTTP_200_OK
        )


class GetProductSortingOptionsV2(APIView):
    available_permission_classes = (
        AnyLoggedInUser,
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        return Response(
            get_sorting_options(),
            status=status.HTTP_200_OK
        )
