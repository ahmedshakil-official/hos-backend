import os, re, operator
from functools import reduce
from elasticsearch_dsl import Q
from validator_collection import checkers
from django.conf import settings
from django.db.models import Prefetch
from django.db.models.functions import Length
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.healthos_helpers import HealthOSHelper
from common.utils import (
    get_days_from_date_range,
    get_day_from_date,
    get_global_based_discarded_list,
    get_global_or_organization_wise_active_list,
    filter_global_product_based_on_settings,
    get_id_fields_based_on_setting,
    convert_bangla_digit_to_english_digit,
    string_to_bool,
)
from common.enums import Status, PublishStatus
from common.healthos_helpers import CustomerHelper, HealthOSHelper
from core.utils import isDate, formatDate, get_global_product_category

from core.permissions import (
    CheckAnyPermission,
    StaffIsAccountant,
    StaffIsAdmin,
    StaffIsLaboratoryInCharge,
    StaffIsNurse,
    StaffIsPhysician,
    StaffIsProcurementOfficer,
    StaffIsReceptionist,
    StaffIsSalesman,
    AnyLoggedInUser,
    IsSuperUser,
    StaffIsSalesReturn,
    StaffIsAdjustment,
    StaffIsTrader,
    StaffIsTelemarketer,
    StaffIsSalesCoordinator,
    StaffIsSalesManager,
    StaffIsDeliveryHub,
    StaffIsDistributionT2,
    StaffIsDistributionT3,
    StaffIsDistributionT1,
    StaffIsFrontDeskProductReturn,
)
from core.enums import AllowOrderFrom
from core.helpers import get_user_profile_details_from_cache

from pharmacy.enums import (
    PurchaseOrderStatus, SalesType,
    ProductGroupType, AdjustmentType, StorePointType,
    DistributorOrderType,
    PurchaseType,
    SystemPlatforms,
)
from pharmacy.models import (
    Stock,
    Product,
)
from pharmacy.utils import (
    filter_data_by_user_permitted_store_points,
    get_sorting_value,
    remove_discount_factor_for_coupon,
    get_product_dynamic_discount_rate,
    get_organization_order_closing_and_reopening_time,
)
from pharmacy.helpers import get_cached_company_ids_of_published_products
from pharmacy.serializers import (
    ProductWithoutStockSerializer,
    ProductFormSerializer,
    ProductManufacturingCompanySerializer,
    ProductGroupSerializer,
    ProductSubgroupSerializer,
    ProductGenericSerializer,
    PurchaseSearchSerializer,
    ProductCategoryModelSerializer,
    StorePointSerializer,
    # StockSerializer,
    StockTransferLiteSerializer,
    StockAdjustmentSearchSerializer,
    UnitSerializer,
)
from pharmacy.custom_serializer.product_disbursement_cause import (
    ProductDisbursementCauseModelSerializer
)
from pharmacy.custom_serializer.stock_adjustment import (
    StockAdjustmentModelSerializer,
)
from pharmacy.custom_serializer.stock import (
    StockSearchBaseSerializer,
)
from pharmacy.custom_serializer.purchase import (
    DistributorOrderListGetSerializer,
)
from search.utils import search_by_multiple_aliases

from..document.pharmacy_search import (
    ProductDocument,
    ProductFormDocument,
    ProductManufacturerDocument,
    ProductGroupDocument,
    ProductSubGroupDocument,
    ProductGenericDocument,
    PurchaseDocument,
    ProductCategoryDocument,
    StorePointDocument,
    EmployeeStorePointDocument,
    # StockDocument,
    StockDisbursementDocument,
    UnitDocument,
    StockDocument,
    PurchaseDocumentForOrder
)


def is_digit_and_id(value):
    return value.isdigit() and len(value) < 10


class ProductSearchView(generics.ListAPIView):
    available_permission_classes = (
        AnyLoggedInUser,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProductWithoutStockSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        is_dict_search = any(map(str.isupper, str(query_value)))
        is_service = self.request.query_params.get('is_service', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = ProductDocument.search()

        stocks = Stock.objects.filter(
            status=Status.ACTIVE,
            organization_id=self.request.user.organization_id,
        ).only(
            'id',
            'product_id',
        )

        aliases = self.request.query_params.get("aliases", None)
        # If aliases exists in the query params then apply filter.
        if aliases:
            alias_list = aliases.split(",")
            search = search.query(
                Q("terms", alias_keyword=alias_list)
            )

        if query_value and not query_value.isdigit():
            if not is_dict_search:
                search = search.query(
                    "multi_match",
                    query=query_value,
                    type="phrase_prefix",
                    fields=[
                        'name',
                        'full_name',
                        'generic.name',
                        'alias_name',
                        'subgroup.name',
                        'subgroup.alias',
                        'alias',
                        'subgroup.product_group.name',
                        'form.name',
                        'manufacturing_company.name'],
                )
            else:
                search = search.query(
                    "multi_match",
                    query=query_value,
                    type="phrase_prefix",
                    fields=['full_name', 'alias_name'],
                )
        elif query_value:
            search = search.query(
                Q("term", id=query_value) | Q("term", stock_id=query_value),
            )

        # if not is_service == 'true':
        #     # if is_service none then return only product
        #     search = search.filter(Q("match", is_service=False))

        search = filter_global_product_based_on_settings(
            self, search, 'search')

        search = search.query(Q('match', status=Status.ACTIVE))
        response = search[:int(page_size)].to_queryset().select_related(
            'organization',
            'primary_unit',
            'secondary_unit',
            'subgroup',
            'subgroup__product_group',
            'manufacturing_company',
            'form',
            'generic',
        ).prefetch_related(
            Prefetch(
                'stock_list',
                queryset = stocks
            )
        ).order_by(Length('name').asc(), 'name')

        if aliases:
            self.pagination_class.page_size = search.count()

        return response


class ProductFormSearchView(generics.ListAPIView):
    available_permission_classes = (
        AnyLoggedInUser,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProductFormSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = ProductFormDocument.search()

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=['name', 'alias']
            )

        q = Q("match", is_global=PublishStatus.INITIALLY_GLOBAL) \
            | Q("match", is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) \
            | Q("match", organization__pk=self.request.user.organization_id)
        search = search.filter(q)
        search = search.query(Q('match', status=Status.ACTIVE))
        skiped_forms = get_global_based_discarded_list(self)
        search = search.exclude('terms', id=skiped_forms)
        response = search[:int(page_size)].execute()
        return response


class ProductManufacturingCompanySearchView(generics.ListAPIView):
    available_permission_classes = (
        AnyLoggedInUser,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProductManufacturingCompanySerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        is_published_products_only = string_to_bool(
            self.request.query_params.get('published_product', None))
        # Quick fix, will remove later
        system_platform = int(
            self.request.META.get("HTTP_X_SYSTEM_PLATFORM", SystemPlatforms.WEB_APP))
        if system_platform == SystemPlatforms.ANDROID_APP:
            is_published_products_only = True
        search = ProductManufacturerDocument.search()
        organization_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)

        aliases = self.request.query_params.get("aliases", None)
        # If aliases exists in the query params then apply filter.
        if aliases:
            alias_list = aliases.split(",")
            search = search.query(
                Q("terms", alias_keyword=alias_list)
            )

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=['name', 'alias'],
                # fuzziness="auto"
            )

        q = Q("match", is_global=PublishStatus.INITIALLY_GLOBAL) \
            | Q("match", is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) \
            | Q("match", organization__pk=organization_id)
        search = search.filter(q)
        search = search.query(Q('match', status=Status.ACTIVE))
        skipped_manufacturer = get_global_based_discarded_list(self, organization=organization_id)
        search = search.exclude('terms', id=skipped_manufacturer)
        if is_published_products_only:
            search = search.filter(
                'terms', id=get_cached_company_ids_of_published_products(self))
            search = search.sort("name.raw")
        # Set the default page size based on the presence of a search keyword.
        page_size = settings.ES_PAGINATION_SIZE if query_value else 500
        response = search[:int(page_size)].execute()
        if aliases:
            default_page_size = settings.REST_FRAMEWORK.get("PAGE_SIZE", 20)
            self.pagination_class.page_size = max(search.count(), default_page_size)
        return response


class ProductGroupSearchView(generics.ListAPIView):
    available_permission_classes = (AnyLoggedInUser,)
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProductGroupSerializer

    def get_queryset(self):
        health_os_helper = HealthOSHelper()
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = ProductGroupDocument.search()

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=['name', 'alias'],
            )

        aliases = self.request.query_params.get("aliases", None)
        # If aliases exists in the query params then apply filter.
        if aliases:
            alias_list = aliases.split(",")
            search = search.query(
                Q("terms", alias_keyword=alias_list)
            )

        q = Q("match", is_global=PublishStatus.INITIALLY_GLOBAL) \
            | Q("match", is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) \
            | Q("match", organization__pk=health_os_helper.organization_id())
        search = search.filter(q)
        search = search.query(Q('match', status=Status.ACTIVE))
        skiped_groups = get_global_based_discarded_list(self)
        search = search.exclude('terms', id=skiped_groups)
        response = search[:int(page_size)].execute()
        return response


class ProductSubgroupSearchView(generics.ListAPIView):
    available_permission_classes = (
        AnyLoggedInUser,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProductSubgroupSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        product_group_alias = self.request.query_params.get('product_group', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = ProductSubGroupDocument.search()

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=['name', 'alias'],
            )
        q = Q("match", is_global=PublishStatus.INITIALLY_GLOBAL) \
            | Q("match", is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) \
            | Q("match", organization__pk=self.request.user.organization_id)
        search = search.filter(q)
        search = search.query(Q('match', status=Status.ACTIVE))
        skiped_groups = get_global_based_discarded_list(self)
        search = search.exclude('terms', id=skiped_groups)
        if product_group_alias:
            # filtering by product group alias if alias if given
            search = search.filter('term', product_group__alias=product_group_alias)

        response = search[:int(page_size)].execute()
        return response


class ProductGenericSearchView(generics.ListAPIView):
    available_permission_classes = (
        AnyLoggedInUser,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProductGenericSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = ProductGenericDocument.search()

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=['name', 'alias'],
            )
        q = Q("match", is_global=PublishStatus.INITIALLY_GLOBAL) \
            | Q("match", is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) \
            | Q("match", organization__pk=self.request.user.organization_id)
        search = search.filter(q)
        search = search.query(Q('match', status=Status.ACTIVE))
        skiped_generics = get_global_based_discarded_list(self)
        search = search.exclude('terms', id=skiped_generics)
        response = search[:int(page_size)].execute()
        return response


class PurchaseSearchView(generics.ListAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
        StaffIsSalesReturn,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = PurchaseSearchSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        query_value = convert_bangla_digit_to_english_digit(query_value)
        supplier = self.request.query_params.get('supplier', None)
        is_sales_return = self.request.query_params.get(
            'is_sales_return', None)
        store = self.request.query_params.get('store_point', None)
        due_purchases = self.request.query_params.get(
            'due_purchases', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)

        search = PurchaseDocument.search()

        if is_sales_return and is_sales_return == 'true':
            search = search.query(Q('match', is_sales_return=True))
        else:
            search = search.query(Q('match', is_sales_return=False))
        if store:
            search = search.query(Q('match', store_point__alias=store))
        if supplier:
            search = search.query(Q('match', person_organization_supplier__alias=supplier))

        if query_value and not is_digit_and_id(query_value):
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=[
                    'alias',
                    'person_organization_receiver.first_name',
                    'person_organization_receiver.last_name',
                    'person_organization_receiver.full_name',
                    'person_organization_supplier.full_name',
                    'person_organization_supplier.company_name',
                    'store_point.name',
                    'organization_department.name',
                ]
            )
        if query_value and is_digit_and_id(query_value):
            search = search.query(
                "multi_match",
                query=query_value,
                type="cross_fields",
                fields=get_id_fields_based_on_setting(
                    self.request.user.organization,
                    ['id'],
                    ['organization_wise_serial']
                )
            )

        search = filter_data_by_user_permitted_store_points(self, search)
        search = search.query(Q("match", organization__id=self.request.user.organization_id)
                              & Q('match', status=Status.ACTIVE)).sort('-purchase_date')

        # get purchases whose total amount is not paid
        if due_purchases:
            search = search.filter(
                'script',
                script="doc['purchase_payment'].value < doc['grand_total'].value"
            )


        response = search[:int(page_size)].execute()
        return response


class ProductCategorySearchView(generics.ListAPIView):
    available_permission_classes = (
        AnyLoggedInUser,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProductCategoryModelSerializer.List

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = ProductCategoryDocument.search()

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=['name', 'alias'],
            )

        q = Q("match", is_global=PublishStatus.INITIALLY_GLOBAL)\
            | Q("match", is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL)\
            | Q("match", organization__pk=self.request.user.organization_id)
        search = search.filter(q)
        search = search.query(Q('match', status=Status.ACTIVE))
        skiped_groups = get_global_based_discarded_list(self)
        search = search.exclude('terms', id=skiped_groups)
        response = search[:int(page_size)].execute()
        return response


class PurchaseOrderPendingSearchView(generics.ListAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = PurchaseSearchSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = PurchaseDocument.search()

        if query_value and not query_value.isdigit():
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=[
                    'person_organization_receiver.first_name',
                    'person_organization_receiver.last_name',
                    'person_organization_receiver.full_name',
                    'person_organization_supplier.full_name',
                    'person_organization_supplier.company_name',
                    'store_point.name',
                    'organization_department.name',
                ]
            )
        elif query_value and query_value.isdigit():
            search = search.query(
                "multi_match",
                query=query_value,
                type="cross_fields",
                fields=get_id_fields_based_on_setting(
                    self.request.user.organization,
                    ['id'],
                    ['organization_wise_serial']
                )
            )

        search = filter_data_by_user_permitted_store_points(self, search)
        search = search.query(
            Q("match", organization__id=self.request.user.organization_id)
            & Q('match', status=Status.PURCHASE_ORDER)
            & Q('match', purchase_order_status=PurchaseOrderStatus.PENDING)
            ).sort('-purchase_date')

        if page_size == 'showall':
            self.pagination_class = None
            response = search[:int(settings.ES_MAX_PAGINATION_SIZE)].execute()
        else:
            response = search[:int(page_size)].execute()
        return response


class PurchaseOrderCompletedSearchView(generics.ListAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = PurchaseSearchSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = PurchaseDocument.search()

        if query_value and not query_value.isdigit():
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=[
                    'person_organization_receiver.first_name',
                    'person_organization_receiver.last_name',
                    'person_organization_receiver.full_name',
                    'person_organization_supplier.company_name',
                    'person_organization_supplier.full_name',
                    'store_point.name',
                    'organization_department.name',
                ]
            )
        elif query_value and query_value.isdigit():
            search = search.query(
                "multi_match",
                query=query_value,
                type="cross_fields",
                fields=get_id_fields_based_on_setting(
                    self.request.user.organization,
                    ['id'],
                    ['organization_wise_serial']
                )
            )

        search = filter_data_by_user_permitted_store_points(self, search)
        search = search.query(
            Q("match", organization__id=self.request.user.organization_id)
            & Q('match', status=Status.PURCHASE_ORDER)
            & Q('match', purchase_order_status=PurchaseOrderStatus.COMPLETED)
            ).sort('-purchase_date')

        if page_size == 'showall':
            self.pagination_class = None
            response = search[:int(settings.ES_MAX_PAGINATION_SIZE)].execute()
        else:
            response = search[:int(page_size)].execute()
        return response


class PurchaseOrderDiscardedSearchView(generics.ListAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = PurchaseSearchSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = PurchaseDocument.search()

        if query_value and not query_value.isdigit():
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=[
                    'person_organization_receiver.first_name',
                    'person_organization_receiver.last_name',
                    'person_organization_receiver.full_name',
                    'person_organization_supplier.company_name',
                    'person_organization_supplier.full_name',
                    'store_point.name',
                    'organization_department.name',
                ]
            )
        elif query_value and query_value.isdigit():
            search = search.query(
                "multi_match",
                query=query_value,
                type="cross_fields",
                fields=get_id_fields_based_on_setting(
                    self.request.user.organization,
                    ['id'],
                    ['organization_wise_serial']
                )
            )

        search = filter_data_by_user_permitted_store_points(self, search)
        search = search.query(
            Q("match", organization__id=self.request.user.organization_id)
            & Q('match', status=Status.PURCHASE_ORDER)
            & Q('match', purchase_order_status=PurchaseOrderStatus.DISCARDED)
            ).sort('-purchase_date')

        response = search[:int(page_size)].execute()
        return response


class DistributorOrderSearchView(generics.ListAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsSalesman,
        StaffIsAdmin,
        StaffIsTrader,
        StaffIsTelemarketer,
        StaffIsSalesCoordinator,
        StaffIsSalesManager,
        StaffIsDeliveryHub,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsFrontDeskProductReturn,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = DistributorOrderListGetSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        organization = self.request.query_params.get('organization', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = PurchaseDocumentForOrder.search()

        if query_value and not query_value.isdigit():
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=[
                    'organization.name',
                    'organization.primary_mobile',
                ]
            )
        elif query_value and query_value.isdigit():
            search = search.query(
                "multi_match",
                query=query_value,
                type="cross_fields",
                fields=['id']
            )

        # search = filter_data_by_user_permitted_store_points(self, search)
        if organization:
            search = search.query(Q('match', organization__id=organization))
        search = search.query(
            Q("match", distributor__id=self.request.user.organization_id)
            & Q('match', status=Status.DISTRIBUTOR_ORDER)
            & Q('match', distributor_order_type=DistributorOrderType.ORDER)
            & Q('match', purchase_type=PurchaseType.VENDOR_ORDER),
        ).sort('-purchase_date')

        response = search[:int(page_size)].execute()
        return response


class PurchaseRequisitionSearchView(generics.ListAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsNurse,
        StaffIsAdmin,
        StaffIsDistributionT1
    )
    permission_classes = (CheckAnyPermission,)

    serializer_class = PurchaseSearchSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        store_point = self.request.query_params.get('store_point', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = PurchaseDocument.search()

        if query_value and not query_value.isdigit():
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=[
                    'person_organization_receiver.first_name',
                    'person_organization_receiver.last_name',
                    'person_organization_receiver.full_name',
                    'person_organization_supplier.company_name',
                    'person_organization_supplier.full_name',
                    'store_point.name',
                    'department.name',
                ]
            )
        elif query_value and query_value.isdigit():
            search = search.query(
                "multi_match",
                query=query_value,
                type="cross_fields",
                fields=get_id_fields_based_on_setting(
                    self.request.user.organization,
                    ['id'],
                    ['organization_wise_serial']
                )
            )
        search = search.query(
            Q('match', organization__id=self.request.user.organization_id)
            & Q('match', status=Status.DRAFT)).sort('-purchase_date')

        if store_point:
            search = search.query(Q('match', store_point__alias=store_point))
        response = search[:int(page_size)].execute()
        return response


class StorePointSearchView(generics.ListAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsSalesman,
        StaffIsNurse,
        StaffIsSalesReturn,
        StaffIsAdjustment,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = StorePointSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = StorePointDocument.search()
        product = self.request.query_params.get('product', None)

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=['name', 'alias'],
            )
        search = filter_data_by_user_permitted_store_points(self, search, primary=True)
        search = search.query(
            Q('match', organization__pk=self.request.user.organization_id)
            & Q('match', status=Status.ACTIVE)
            # & ~Q('match', type=StorePointType.VENDOR_DEFAULT)
        )

        if product:
            store_points = Stock.objects.filter(
                status=Status.ACTIVE,
                organization=self.request.user.organization_id,
                product__alias=product,
            ).values_list('store_point__pk', flat=True)
            search = search.filter('terms', id=list(set(store_points)))

        if page_size == 'showall':
            self.pagination_class = None
            response = search[:int(settings.ES_MAX_PAGINATION_SIZE)].execute()
        else:
            response = search[:int(page_size)].execute()
        return response


class EmployeeStorePointSearchView(generics.ListAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsSalesman,
        StaffIsNurse,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = StorePointSerializer
    lookup_field = 'employee-alias'

    def get_queryset(self):
        employee_alias = self.kwargs['employee_alias']
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = EmployeeStorePointDocument.search()

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=['store_point.name', 'store_point.alias'],
            )
        search = search.query(
            Q('match', organization__pk=self.request.user.organization_id)
            & Q('match', employee__alias=employee_alias)
            & Q('match', access_status=True))
        response = search[:int(page_size)].execute()
        store_points = list(set([item.store_point for item in response]))
        serializer = StorePointSerializer(store_points, many="true")
        return serializer.data


class StockDisbursementSearchView(generics.ListAPIView):
    available_permission_classes = (AnyLoggedInUser,)
    permission_classes = (CheckAnyPermission,)
    serializer_class = StockAdjustmentSearchSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = StockDisbursementDocument.search()

        if query_value:
            if not is_digit_and_id(query_value):
                search = search.query(
                    "multi_match",
                    query=query_value,
                    type="phrase_prefix",
                    fields=[
                        'person_organization_employee.first_name',
                        'person_organization_employee.last_name',
                        'person_organization_employee.full_name',
                        'person_organization_employee.phone',
                        'person_organization_patient.first_name',
                        'person_organization_patient.last_name',
                        'person_organization_patient.full_name',
                        'person_organization_patient.phone',
                        'person_organization_patient.code',
                        'store_point.name',
                        'service_consumed.subservice.name'
                    ]
                )
            else:
                search = search.query(
                    "multi_match",
                    query=query_value,
                    type="cross_fields",
                    fields=['id', 'person_organization_patient.phone']
                )
        q = Q("match", organization__pk=self.request.user.organization_id) \
            & Q('match', status=Status.ACTIVE) \
            & Q('match', is_product_disbrustment=True)
        search = search.filter(q)
        search = filter_data_by_user_permitted_store_points(self, search)
        if page_size == 'showall':
            self.pagination_class = None
            response = search[:int(settings.ES_MAX_PAGINATION_SIZE)].execute()
        else:
            response = search[:int(page_size)].execute()
        return response


class StockAdjustmentSearchView(generics.ListAPIView):
    available_permission_classes = (AnyLoggedInUser,)
    permission_classes = (CheckAnyPermission,)
    serializer_class = StockAdjustmentModelSerializer.List

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = StockDisbursementDocument.search()

        if query_value and not is_digit_and_id(query_value):
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=['person_organization_employee.first_name',
                        'person_organization_employee.last_name',
                        'person_organization_employee.full_name',
                        'store_point.name',
                        'person_organization_patient.first_name',
                        'person_organization_patient.last_name',
                        'person_organization_patient.full_name',
                        'person_organization_patient.code',
                        'person_organization_patient.phone']
            )
        elif query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="cross_fields",
                fields=[
                    'id',
                    'person_organization_patient.phone'
                ]
            )
        q = Q("match", organization__pk=self.request.user.organization_id) \
            & Q('match', status=Status.ACTIVE) \
            & Q('match', is_product_disbrustment=False) \
            & ~Q('match', adjustment_type=AdjustmentType.AUTO)
        search = search.filter(q)

        search = filter_data_by_user_permitted_store_points(self, search)
        if page_size == 'max':
            self.pagination_class = None
            response = search[:int(settings.ES_MAX_PAGINATION_SIZE)].execute()
        else:
            response = search[:int(page_size)].execute()
        return response


class UnitSearchView(generics.ListAPIView):
    available_permission_classes = (
        AnyLoggedInUser,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = UnitSerializer

    def get_queryset(self):
        query_value = self.request.query_params.get('keyword', None)
        product = self.request.query_params.get('product', None)
        page_size = self.request.query_params.get(
            'page_size', settings.ES_PAGINATION_SIZE)
        search = UnitDocument.search()

        skiped_units = get_global_based_discarded_list(self)

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                type="phrase_prefix",
                fields=['name']
            )

        search = search.query(
            Q('match', status=Status.ACTIVE) &
            (Q("match", organization__pk=self.request.user.organization_id)
            | Q("match", is_global=PublishStatus.INITIALLY_GLOBAL)
            | Q("match", is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL))
        )

        if checkers.is_uuid(product):
            units = Product.objects.values_list(
                'primary_unit', 'secondary_unit'
            ).filter(alias=product)
            search = search.filter(
                "terms", id=[item for item in units.first()])
        search = search.exclude('terms', id=skiped_units)
        if page_size == 'showall':
            self.pagination_class = None
            response = search[:int(settings.ES_MAX_PAGINATION_SIZE)].execute()
        if page_size != 'showall':
            response = search[:int(page_size)].execute()
        return response


class ECommerceStockProductSearchView(generics.ListAPIView):
    available_permission_classes = (AnyLoggedInUser,)
    permission_classes = (CheckAnyPermission,)
    serializer_class = StockSearchBaseSerializer.ECommerceStockProductSearch
    def filter_availability(self, search):
        # Extracting the 'product_groups' parameter from the request query parameters i.e category
        category = self.request.query_params.get("category", None)

        # Checking if 'product_group' has a valid value (i.e., not None or empty)
        if category:
            # Filtering the 'search' based on the 'product_groups' value (i.e., alias)
            product_category_list = category.split(",")
            search = search.filter(
                "terms", product__subgroup__product_group__alias=product_category_list
            )
        setting = HealthOSHelper().settings()
        product_availability = self.request.GET.get("availability", "")

        # if not setting.overwrite_order_mode_by_product and setting.allow_order_from == AllowOrderFrom.STOCK_AND_OPEN and not product_availability:
        #     # Applying filters to exclude products with is_queueing_item=True
        #     search = search.filter(
        #         ~Q("match", product__is_queueing_item=True) &
        #         (
        #             Q("match", product__order_mode=AllowOrderFrom.STOCK) |
        #             Q("match", product__order_mode=AllowOrderFrom.OPEN) |
        #             Q("range", orderable_stock={"gt": 0})
        #         )
        #     )
        #     return search

        values = re.split(r',\s*', product_availability)
        if "PRE_ORDER" in values and 'IN_STOCK' in values:
            search = search.exclude(
                Q("match", current_order_mode=AllowOrderFrom.STOCK) &
                Q("range", **{"orderable_stock": {"lte": 0}})
            )
            return search.exclude(
                Q("match", product__is_salesable=False) |
                Q("match", is_out_of_stock=True)
            )
        elif "IN_STOCK" in values:
            search = search.exclude(
                Q("match", current_order_mode=AllowOrderFrom.STOCK) &
                Q("range", **{"orderable_stock": {"lte": 0}})
            )
            search = search.exclude(
                Q("match", product__is_salesable=False) |
                Q("match", is_out_of_stock=True)
            )
            return search.filter(
                Q("match", product__is_queueing_item=False)
            )
        elif "PRE_ORDER" in values:
            search = search.exclude(
                Q("match", current_order_mode=AllowOrderFrom.STOCK) &
                Q("range", **{"orderable_stock": {"lte": 0}})
            )
            search = search.exclude(
                Q("match", product__is_salesable=False) |
                Q("match", is_out_of_stock=True)
            )
            return search.filter(
                Q("match", product__is_queueing_item=True)
            )
        # elif "STOCK_AND_OPEN" in values:
        #     # Applying filters to exclude products with is_queueing_item=True
        #     search = search.filter(
        #         ~Q("match", product__is_queueing_item=True) &  # Excluding products with is_queueing_item=True
        #         (
        #             Q("match", product__order_mode=AllowOrderFrom.STOCK) |
        #             Q("match", product__order_mode=AllowOrderFrom.OPEN) |
        #             Q("range", orderable_stock={"gt": 0})  # Filtering for orderable_stock > 0
        #         )
        #     )
        #     return search
        else:
            return search

    def get_queryset(self):
        aliases = self.request.GET.get("aliases", None)
        query_value = self.request.query_params.get("keyword", None)
        manufacturing_company_aliases = self.request.query_params.get("manufacturing_company", None)
        user_details = get_user_profile_details_from_cache(self.request.user.id)
        page_size = self.request.query_params.get(
            "page_size", settings.ES_PAGINATION_SIZE
        )
        product_availability = self.request.GET.get("availability", "")
        values = re.split(r',\s*', product_availability)
        sort_by = self.request.GET.get("sort_by", "")
        sort_by = [str(get_sorting_value(sort_by, is_es_sorting=True))] if get_sorting_value(sort_by, is_es_sorting=True) else []
        filters = []
        excludes = []

        # Create an object of the HealthOSHelper class
        healthos_helper = HealthOSHelper()

        # Get a list of the top sold stocks' primary key (PK) IDs
        top_sold_stocks_ids = healthos_helper.get_top_sold_stocks_pk_list()

        if (sort_by and len(sort_by) == 1 and "-product.discount_rate" in sort_by and
                aliases is None and manufacturing_company_aliases is None and
                query_value is None and values == ['']):
            # Apply a filter it to include only records with IDs in top_sold_stocks_ids
            # when sorting by"-product.discount_rate".

            filters.append(
                Q("terms", id=top_sold_stocks_ids)
            )

        filters.append(Q("match", status=Status.ACTIVE))
        filters.append(Q("match", store_point__pk=408))
        filters.append(Q("match", organization__pk=303))
        filters.append(Q("match", product__is_published=True))

        if manufacturing_company_aliases:
            manufacturing_company_aliases = manufacturing_company_aliases.split(",")
            filters.append(
                Q("terms", product__manufacturing_company__alias=manufacturing_company_aliases)
            )

        search = StockDocument.search()
        search = search.filter(reduce(operator.iand, filters))
        search = self.filter_availability(search)

        if aliases:
            aliases = aliases.split(",")
            search = search.filter(Q("terms", alias=aliases))

        # if healthos_settings.allow_order_from == AllowOrderFrom.STOCK and not healthos_settings.overwrite_order_mode_by_product:
        #     excludes.append(Q("match", product__is_queueing_item=True))
        # elif healthos_settings.overwrite_order_mode_by_product:
        #     excludes.append(Q("match", product__is_queueing_item=True))
        #     excludes.append(Q("match", product__order_mode=AllowOrderFrom.STOCK))
        if excludes:
            search = search.exclude(reduce(operator.iand, excludes))
        # filter product order limit value based on delivery hub short_code
        try:
            short_code = user_details.organization.delivery_hub.short_code
            if short_code == "MH-1":
                search = search.exclude(Q("match", product__order_limit_per_day_mirpur=0))
            elif short_code == "UH-1":
                search = search.exclude(Q("match", product__order_limit_per_day_uttara=0))
            else:
                search = search.exclude(Q("match", product__order_limit_per_day=0))
        except:
            search = search.exclude(Q("match", product__order_limit_per_day=0))

        if query_value:
            search = search.query(
                "multi_match",
                query=query_value,
                # type="phrase_prefix",
                fields=[
                    "product.name_not_analyzed^100",
                    "product.name^5",
                    "product.full_name^4",
                    "product.display_name^3",
                    "product.manufacturing_company.name^2",
                    "product.generic.name^1",
                ],
                fuzziness="auto:4,8",
                # prefix_length=2,
                max_expansions=50,
                type="best_fields",
                tie_breaker=0.9,
            )
        else:
            search = search.filter(Q("match", product__is_salesable=True))
            search = search.exclude(Q("match", is_out_of_stock=True))
        search.query = Q("function_score", query=search.query, field_value_factor={
            "field": "ranking",
            "missing": 1
        })
        sort_by.append({"_score" : {"order" : "desc"}})
        # sort_by.append({"product.is_salesable" : {"order" : "desc"}})
        search = search.sort(*sort_by)
        response = search[:int(page_size)].execute()
        return response

    def get(self, request, *args, **kwargs):
        finalize_response = self.finalize_response(
            request= request,
            response=self.list(request, *args, **kwargs)
        ).data
        results = finalize_response["results"]
        # check if order is disabled
        order_closing_date, order_reopening_date = get_organization_order_closing_and_reopening_time()
        is_order_enabled = not order_closing_date and not order_reopening_date

        # as per organization/user cumulative_discount_factor is different
        for item in results:
            item["product"]["discount_rate_factor"] = remove_discount_factor_for_coupon(
                request=request,
                data=item
            )
            item["product"]["dynamic_discount_rate"] = get_product_dynamic_discount_rate(
                user_org_id=request.user.organization_id,
                stock_id=item["id"],
                trading_price=item["product"]["trading_price"],
                discount_rate=item["product"]["discount_rate"]
            )
            item["product"]["dynamic_discount_factors"] = CustomerHelper(
                organization_id=request.user.organization_id
            ).get_organization_and_area_discount()
            # update is_order_enabled value
            item["is_order_enabled"] = is_order_enabled
        return Response(finalize_response, status=status.HTTP_200_OK)


class ECommerceStockProductSearchSuggestView(APIView):
    authentication_classes = [] #disables authentication
    permission_classes = []

    def get(self, request):
        query_value = self.request.query_params.get("keyword", None)
        page_size = self.request.query_params.get(
            "page_size", settings.ES_PAGINATION_SIZE
        )

        search = StockDocument.search()
        completion = {
            "field": "product.full_name.suggest",
            "size": 6,
            "skip_duplicates": True,
            "fuzzy": {
                "fuzziness": "auto:4,8"
            },

        }
        if query_value:
            suggest = search.suggest(
                "auto_complete",
                query_value,
                completion=completion
            )
            suggest = suggest.source(
                includes=[
                    "status",
                    "product.is_published",
                    "product.order_limit_per_day",
                ]
            )
            suggest = suggest[:int(page_size)].execute()
            try:
                options = suggest.suggest.auto_complete[0]["options"]
            except:
                options = []
            results = [item.text for item in options if not (item._source["product"]["is_published"] == False or item._source["status"] == Status.INACTIVE or item._source["product"]["order_limit_per_day"] < 1)]
        else:
            results = []
        return Response(
            results,
            status=status.HTTP_200_OK
        )


class ECommerceStockProductSearchSuggestViewV2(APIView):
    authentication_classes = [] #disables authentication
    permission_classes = []

    def get(self, request):
        query_value = self.request.query_params.get("keyword", None)
        page_size = self.request.query_params.get(
            "page_size", settings.ES_PAGINATION_SIZE
        )

        search = StockDocument.search()
        completion = {
            "field": "product.full_name.suggest",
            "size": 6,
            "skip_duplicates": True,
            "fuzzy": {
                "fuzziness": "auto:4,8"
            },

        }
        if query_value:
            suggest = search.suggest(
                "auto_complete",
                query_value,
                completion=completion
            )
            suggest = suggest.source(
                includes=[
                    "status",
                    "product.is_published",
                    "product.order_limit_per_day",
                    "product.form.name"
                ]
            )
            suggest = suggest[:int(page_size)].execute()
            try:
                options = suggest.suggest.auto_complete[0]["options"]
            except:
                options = []
            results = [
                {
                    "full_name": item["text"],
                    "form": item["_source"]["product"]["form"]["name"]
                    if "product" in item["_source"] and "form" in item["_source"]["product"]
                    else "",
                }
                for item in options
                if not (
                    item._source["product"]["is_published"] == False
                    or item._source["status"] == Status.INACTIVE
                    or item._source["product"]["order_limit_per_day"] < 1
                )
            ]
        else:
            results = []
        return Response(
            results,
            status=status.HTTP_200_OK
        )


class ProductGroupSearchViewV2(generics.ListAPIView):
    available_permission_classes = (AnyLoggedInUser,)
    permission_classes = (CheckAnyPermission,)
    serializer_class = ProductGroupSerializer

    def get_queryset(self):
        health_os_helper = HealthOSHelper()
        page_size = self.request.query_params.get(
            "page_size", settings.ES_PAGINATION_SIZE)
        search = ProductGroupDocument.search()
        q = Q("match", organization__pk=health_os_helper.organization_id())
        search = search.filter(q)
        search = search.filter("exists", field="logo")
        search = search.query(Q("match", status=Status.ACTIVE))
        search = search.sort("name.raw")
        response = search[:int(page_size)].execute()
        return response
