# for python3 compatibility
from __future__ import division

import datetime
import logging
import json
from validator_collection import checkers
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from django.db.models import (
    Case,
    F,
    Q,
    Sum,
    When,
    Prefetch,
    FloatField,
    Count,
    fields,
    Value,
    Max,
    Subquery,
    Min,
    Func,
    ExpressionWrapper,
)
from django.db.models.functions import Coalesce, Cast, Length, ExtractHour, ExtractMinute, Concat
from django.db.models.functions.comparison import NullIf
from django.db.utils import IntegrityError
from django.http import QueryDict
from rest_framework import status
from rest_framework.serializers import (ValidationError, )
from rest_framework.generics import (
    CreateAPIView, ListAPIView,
    RetrieveUpdateDestroyAPIView
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from common.pagination import CachedCountPageNumberPagination
from common import helpers
from common.utils import (
    create_cache_key_name,
    get_global_based_discarded_list,
    filter_global_product_based_on_settings,
    generate_code_with_hex_of_organization_id,
    create_bulk_transaction,
    isclose,
    prepare_start_date,
    prepare_end_date,
    get_datetime_obj_from_datetime_str,
    create_discarded_item,
    not_blank,
    validate_uuid4,
    sync_queryset,
    re_validate_grand_total,
    get_healthos_settings,
)
from common.enums import Status, PublishStatus, DiscardType
from common.tasks import cache_expire_list

from core.permissions import (
    CheckAnyPermission,
    StaffIsAdmin,
    StaffIsNurse,
    StaffIsProcurementOfficer,
    StaffIsSalesman,
    StaffIsReceptionist,
    StaffIsAccountant,
    StaffIsLaboratoryInCharge,
    IsSuperUser,
    StaffIsMonitor,
    StaffIsSalesReturn,
    StaffIsAdjustment,
    StaffIsTelemarketer,
    StaffIsProcurementManager,
    StaffIsDeliveryHub,
    StaffIsDistributionT1,
    StaffIsSalesCoordinator,
    StaffIsDistributionT2,
    StaffIsDistributionT3,
    StaffIsFrontDeskProductReturn,
    StaffIsSalesManager,
    StaffIsProcurementCoordinator,
)

from core.enums import PriceType, PersonGroupType, AllowOrderFrom, OrganizationType
from core.helpers import get_user_profile_details_from_cache
from core.models import OrganizationSetting, PersonOrganization

from core.views.common_view import(
    ListCreateAPICustomView,
    RetrieveUpdateDestroyAPICustomView,
    ListAPICustomView
)
from account.models import Transaction, TransactionPurchase
from .enums import (
    StockIOType,
    PurchaseOrderStatus,
    PurchaseType,
    AdjustmentType,
    SalesModeType,
    InventoryType,
    SalesType,
    SalesInactiveType,
    StorePointType,
    DistributorOrderType,
    OrderTrackingStatus,
)
from .utils import (
    # get_latest_io_logs_of_stocks,
    prepare_for_sales_graph,
    get_product_store_wise_stock,
    update_stock_calculated_price,
    create_item_with_clone_and_replace_clone_items,
    filter_data_by_user_permitted_store_points,
    stock_specific_attribute_filter,
    merge_two_products,
)
from .filters import (
    StockDisbursementFilter,
    PurchaseRequisitionFilter,
    StockTransferRequisitionFilter,
    StockTransferFilter,
    SalesFilter,
    PurchaseListFilter,
    PurchaseOrderListFilter,
    StockAdjustmentFilter,
    PurchaseSummaryFilter,
)

from .models import (
    EmployeeStorepointAccess,
    Product,
    ProductForm,
    ProductGeneric,
    ProductCategory,
    ProductGroup,
    ProductManufacturingCompany,
    ProductSubgroup,
    Purchase,
    Sales,
    Stock,
    StockAdjustment,
    StockIOLog,
    StockTransfer,
    StorePoint,
    EmployeeAccountAccess,
    StoreProductCategory,
    StockIOLogDisbursementCause,
    Unit,
    OrganizationWiseDiscardedProduct,
    PurchaseRequisition,
)
from .serializers import (
    EmployeeStorepointAccessBasicSerializer,
    EmployeeStorepointAccessSerializer,
    ProductBasicSerializer,
    ProductWithoutStockLiteSerializer,
    PossibleDuplicateProductSerializer,
    ProductFormSerializer,
    ProductGenericSerializer,
    ProductGroupSerializer,
    ProductManufacturingCompanySerializer,
    ProductSubgroupBasicSerializer,
    ProductSubgroupSerializer,
    ProductWithStockSerializer,
    ProductOpeningStockSerializer,
    PurchaseDetailsSerializer,
    PurchaseSerializer,
    PurchaseBasicSerializer,
    StockAdjustmentBasicSerializer,
    StockAdjustmentSerializer,
    StockBasicSerializer,
    StockWithStorePointSerializer,
    StockIOLogBatchWiseDateSerializer,
    StockSerializer,
    StockWithProductUnitSerializer,
    StockAdjustmentDetailsSerializer,
    StockAdjustmentDetailsForDisburseSerializer,
    StockTransferDetailsSerializer,
    StockTransferSerializer,
    StorePointSerializer,
    StockIOReportSerializer,
    StockWithProductForRequisitionSerializer,
    StockReportSerializer,
    StockReportBatchWiseSerializer,
    StockProfitReportSerializer,
    StockProfitReportSummarySerializer,
    ProductStockReportSerializer,
    InventorySummarySerializer,
    EmployeeAccountAccessBasicSerializer,
    EmployeeAccountAccessSerializer,
    StockIOLogBatchWiseSerializer,
    WithoutStockIOLogBatchWiseSerializer,
    StockIOLogSerializer,
    PurchaseListSerializer,
    PurchaseRequisitionSerializer,
    SalesReturnSerializer,
    PurchaseReturnSerializer,
    PurchaseListGetSerializer,
    StockDisbursementListSerializer,
    StockDetailsReportSerializer,
    StockTransferLiteSerializer,
    StockTransferRequisitionSerializer,
    PurchaseOrderReportSerializer,
    UnitSerializer,
    ProductMergeSerializer,
    # StockAdjustmentListSerializer,
    StorePointWithCategorySerializer,
    StoreProductCategorySerializer,
    StoreWiseSalesGraphSerializer,
    CompanyWiseSalesGraphSerializer,
    UnitMergeSerializer,
    ProductLastUsageDateSerializer,
)


from .custom_serializer.purchase import PurchaseSummarySerializer, PurchaseRequisitionListGetSerializer
from .custom_serializer.stock_io_log import StockIoLogReportSerializer
from .custom_serializer.product_category import (
    ProductCategoryModelSerializer,
)
from .custom_serializer.product_disbursement_cause import (
    ProductDisbursementCauseModelSerializer
)
from .custom_serializer.stock import (
    ProductShortReportSerializer,
    StockReportDemandSerializer,
    StoreWiseStockValueSerializer
)
from .custom_serializer.stock_adjustment import StockAdjustmentModelSerializer

from .helpers import (
    stop_inventory_signal,
    start_inventory_signal,
    add_log_price_on_stock_queryset
)
from .tasks import update_stock_related_data_for_purchase_lazy

logger = logging.getLogger(__name__)


class Round(Func):
    function = "ROUND"


class ProductFormList(ListCreateAPICustomView):
    serializer_class = ProductFormSerializer
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (
        CheckAnyPermission,
    )
    cache_name = 'list'
    cached_model_name = 'product_form'
    deleted_cache_model_list = [cached_model_name]

    def get_queryset(self):
        queryset = super(ProductFormList, self).get_queryset()
        skiped_forms = get_global_based_discarded_list(self)
        return queryset.exclude(pk__in=skiped_forms)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = create_item_with_clone_and_replace_clone_items(
                    self, request, 'form', Product)

                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


# class ProductFormSearch(OrganizationAndGlobalWiseSearch):
#     serializer_class = ProductFormSerializer
#     permission_classes = (StaffIsAdmin, )
#     model_name = ProductForm

#     def get_queryset(self):
#         return self.serve_queryset(self)


class ProductFormDetails(RetrieveUpdateDestroyAPICustomView):
    queryset = ProductForm.objects.filter(status=Status.ACTIVE)
    serializer_class = ProductFormSerializer
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (
        CheckAnyPermission,
    )
    lookup_field = 'alias'
    deleted_cache_model_list = ['product_form']


class ProductManufacturingCompanyList(ListCreateAPICustomView):
    serializer_class = ProductManufacturingCompanySerializer
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementOfficer,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (
        CheckAnyPermission,
    )
    cache_name = 'list'
    cached_model_name = 'product_manufacturing_company'
    deleted_cache_model_list = [cached_model_name]

    def get_queryset(self):
        queryset = super(ProductManufacturingCompanyList, self).get_queryset()
        skiped_forms = get_global_based_discarded_list(self)
        return queryset.exclude(pk__in=skiped_forms)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = create_item_with_clone_and_replace_clone_items(
                    self, request, 'manufacturing_company', Product)

                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


# class ProductManufacturingCompanySearch(OrganizationAndGlobalWiseSearch):
#     serializer_class = ProductManufacturingCompanySerializer
#     permission_classes = (StaffIsAdmin, )
#     model_name = ProductManufacturingCompany

#     def get_queryset(self):
#         return self.serve_queryset(self)


class ProductManufacturingCompanyDetails(RetrieveUpdateDestroyAPICustomView):
    queryset = ProductManufacturingCompany.objects.filter(status=Status.ACTIVE)
    serializer_class = ProductManufacturingCompanySerializer
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementOfficer,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (
        CheckAnyPermission,
    )
    lookup_field = 'alias'
    deleted_cache_model_list = ['product_manufacturing_company']


class ProductGroupList(ListCreateAPICustomView):
    serializer_class = ProductGroupSerializer
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission,)
    cache_name = 'list'
    cached_model_name = 'product_group'
    deleted_cache_model_list = [cached_model_name]

    def get_queryset(self):
        queryset = super(ProductGroupList, self).get_queryset()
        skiped_groups = get_global_based_discarded_list(self)
        return queryset.exclude(pk__in=skiped_groups)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = create_item_with_clone_and_replace_clone_items(
                    self, request, 'product_group', ProductSubgroup)

                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

# class ProductGroupSearch(OrganizationAndGlobalWiseSearch):
#     serializer_class = ProductGroupSerializer
#     permission_classes = (StaffIsAdmin, )
#     model_name = ProductGroup

#     def get_queryset(self):
#         return self.serve_queryset(self)


class ProductGroupDetails(RetrieveUpdateDestroyAPICustomView):
    queryset = ProductGroup.objects.filter(status=Status.ACTIVE)
    serializer_class = ProductGroupSerializer
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission,)
    lookup_field = 'alias'
    deleted_cache_model_list = ['product_group']


class ProductSubgroupList(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission,)
    cache_name = 'list'
    cached_model_name = 'product_subgroup'
    deleted_cache_model_list = [cached_model_name]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductSubgroupSerializer
        else:
            return ProductSubgroupBasicSerializer

    def get_queryset(self):
        select_related = ['product_group']
        select_only = []
        queryset = super(ProductSubgroupList, self).get_queryset(
            select_related,
            select_only
        )
        skiped_sub_groups = get_global_based_discarded_list(self)
        return queryset.exclude(pk__in=skiped_sub_groups)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = create_item_with_clone_and_replace_clone_items(
                    self, request, 'subgroup', Product)

                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


# class ProductSubgroupSearch(OrganizationAndGlobalWiseSearch):
#     serializer_class = ProductSubgroupSerializer
#     permission_classes = (StaffIsAdmin, )
#     model_name = ProductSubgroup

#     def get_queryset(self):
#         return self.serve_queryset(self)


class ProductSubgroupDetails(RetrieveUpdateDestroyAPICustomView):
    queryset = ProductSubgroup.objects.filter(status=Status.ACTIVE)
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission,)
    lookup_field = 'alias'
    deleted_cache_model_list = ['product_sub_group']

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductSubgroupSerializer
        else:
            return ProductSubgroupBasicSerializer


class ProductGenericList(ListCreateAPICustomView):
    serializer_class = ProductGenericSerializer
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementOfficer,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (
        CheckAnyPermission,
    )
    cache_name = 'list'
    cached_model_name = 'product_generic'
    deleted_cache_model_list = [cached_model_name]

    def get_queryset(self):
        queryset = super(ProductGenericList, self).get_queryset()
        skiped_generics = get_global_based_discarded_list(self)
        return queryset.exclude(pk__in=skiped_generics)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = create_item_with_clone_and_replace_clone_items(
                    self, request, 'generic', Product)

                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


# class ProductGenericSearch(ListAPIView):
#     serializer_class = ProductGenericSerializer
#     permission_classes = (StaffIsAdmin, )
#     model_name = ProductGeneric

#     def get_queryset(self):
#         return self.serve_queryset(self)


class ProductGenericDetails(RetrieveUpdateDestroyAPICustomView):
    queryset = ProductGeneric.objects.filter(status=Status.ACTIVE)
    serializer_class = ProductGenericSerializer
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsProcurementOfficer,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (
        CheckAnyPermission,
    )
    lookup_field = 'alias'
    deleted_cache_model_list = ['product_generic']


class ProductCategoryList(ListCreateAPICustomView):
    serializer_class = ProductCategoryModelSerializer.List
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (
        CheckAnyPermission,
    )

    def get_queryset(self):
        queryset = super(ProductCategoryList, self).get_queryset()
        skiped_generics = get_global_based_discarded_list(self)
        return queryset.exclude(pk__in=skiped_generics)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = create_item_with_clone_and_replace_clone_items(
                    self, request, 'category', Product)
                clone_item = request.data.get('clone_item', None)
                if clone_item:
                    filter_data = StoreProductCategory.objects.filter(
                        status=Status.ACTIVE,
                        organization=self.request.user.organization_id,
                        product_category_id=clone_item['parent']
                    )
                    for item in filter_data:
                        item.product_category_id = serializer.data['id']
                        item.save(update_fields=['product_category', ])

                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)



class ProductCategoryDetails(RetrieveUpdateDestroyAPICustomView):
    queryset = ProductCategory.objects.filter(status=Status.ACTIVE)
    serializer_class = ProductCategoryModelSerializer.Details
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (
        CheckAnyPermission,
    )
    lookup_field = 'alias'


class DiscardedProductList(APIView):
    permission_classes = (StaffIsAdmin, )

    def get(self, request, *args, **kwargs):
        discarded_item = request.user.organization.get_discarded_product()
        return Response(data=discarded_item)


class PossibleDuplicateProductList(ListAPIView):
    """[API for fetching possible duplicate product]

    Arguments:
        ListAPIView {[type]} -- [description]

    Returns:
        [List] -- [List of QuerySet]
    """
    available_permission_classes = (
        StaffIsAdmin,
        IsSuperUser,
        StaffIsProcurementManager,
        StaffIsProcurementOfficer,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = PossibleDuplicateProductSerializer
    def get_queryset(self):
        organization_id = self.request.user.organization_id
        raw_query = '''WITH org_id AS
(
       SELECT {0})
SELECT   NAME,
         organization_id,
         company,
         product_id,
         product_id AS id,
         form_name,
         full_name,
         possible_duplicate,
         COALESCE(used,0) AS used
FROM     (
                   SELECT    core_organization.NAME,
                             product_info.*,
                             stock_count.used
                   FROM      (
                                      SELECT   organization_id,
                                               product_id,
                                               product_id AS id,
                                               company,
                                               form_name,
                                               full_name,
                                               Count(*) - 1 AS possible_duplicate
                                      FROM     (
                                                         SELECT    part_1.*,
                                                                   part_2.bkey,
                                                                   part_2.product_id AS possible_duplicate_product_id
                                                         FROM      (
                                                                             SELECT    product_id,
                                                                                       full_name,
                                                                                       data.organization_id,
                                                                                       pharmacy_productform.NAME                                                                                 AS form_name,
                                                                                       pharmacy_productmanufacturingcompany.NAME                                                                 AS company,
                                                                                       Replace(Replace(Replace(Lower(Concat(full_name, pharmacy_productform.NAME)), ' ', ''), '-', ''), '/', '') AS akey
                                                                             FROM      (
                                                                                                 SELECT    product.*,
                                                                                                           global_product_category
                                                                                                 FROM      (
                                                                                                                  SELECT core_organization.id AS organization_id,
                                                                                                                         pharmacy_product.id  AS product_id,
                                                                                                                         form_id,
                                                                                                                         manufacturing_company_id,
                                                                                                                         full_name,
                                                                                                                         global_category,
                                                                                                                         is_global,
                                                                                                                         pharmacy_product.organization_id AS product_organization_id
                                                                                                                  FROM   core_organization,
                                                                                                                         pharmacy_product
                                                                                                                  WHERE  core_organization.status = {1}
                                                                                                                  AND    pharmacy_product.status = {1}
                                                                                                                  AND    core_organization.id =
                                                                                                                         (
                                                                                                                                SELECT *
                                                                                                                                FROM   org_id)) AS product
                                                                                                 LEFT JOIN core_organizationsetting
                                                                                                 using     (organization_id)
                                                                                                 WHERE     ((
                                                                                                                               product.is_global = {2}
                                                                                                                     AND       product_organization_id = organization_id )
                                                                                                           OR        (
                                                                                                                               product.is_global != {2}
                                                                                                                     AND       global_product_category = global_category ) )
                                                                                                 AND       (
                                                                                                                     product_id NOT IN
                                                                                                                     (
                                                                                                                            SELECT parent_id
                                                                                                                            FROM   pharmacy_organizationwisediscardedproduct
                                                                                                                            WHERE  status = {1}
                                                                                                                            AND    organization_id IN
                                                                                                                                   (
                                                                                                                                          SELECT *
                                                                                                                                          FROM   org_id) ) ) ) AS data
                                                                             LEFT JOIN pharmacy_productform
                                                                             ON        data.form_id = pharmacy_productform.id
                                                                             LEFT JOIN pharmacy_productmanufacturingcompany
                                                                             ON        pharmacy_productmanufacturingcompany.id = manufacturing_company_id ) AS part_1
                                                         LEFT JOIN
                                                                   (
                                                                             SELECT    product_id,
                                                                                       full_name,
                                                                                       data.organization_id,
                                                                                       pharmacy_productform.NAME AS
                                                                             FROM      ,
                                                                                       pharmacy_productmanufacturingcompany.NAME                                                                 AS company,
                                                                                       replace(replace(replace(lower(concat(full_name, pharmacy_productform.NAME)), ' ', ''), '-', ''), '/', '') AS bkey
                                                                             FROM      (
                                                                                                 SELECT    product.*,
                                                                                                           global_product_category
                                                                                                 FROM      (
                                                                                                                  SELECT core_organization.id AS organization_id,
                                                                                                                         pharmacy_product.id  AS product_id,
                                                                                                                         form_id,
                                                                                                                         manufacturing_company_id,
                                                                                                                         full_name,
                                                                                                                         global_category,
                                                                                                                         is_global,
                                                                                                                         pharmacy_product.organization_id AS product_organization_id
                                                                                                                  FROM   core_organization,
                                                                                                                         pharmacy_product
                                                                                                                  WHERE  core_organization.status = {1}
                                                                                                                  AND    pharmacy_product.status = {1}
                                                                                                                  AND    core_organization.id =
                                                                                                                         (
                                                                                                                                SELECT *
                                                                                                                                FROM   org_id)) AS product
                                                                                                 LEFT JOIN core_organizationsetting
                                                                                                 using     (organization_id)
                                                                                                 WHERE     ((
                                                                                                                               product.is_global = {2}
                                                                                                                     AND       product_organization_id = organization_id )
                                                                                                           OR        (
                                                                                                                               product.is_global != {2}
                                                                                                                     AND       global_product_category = global_category ) )
                                                                                                 AND       (
                                                                                                                     product_id NOT IN
                                                                                                                     (
                                                                                                                            SELECT parent_id
                                                                                                                            FROM   pharmacy_organizationwisediscardedproduct
                                                                                                                            WHERE  status = {1}
                                                                                                                            AND    organization_id IN
                                                                                                                                   (
                                                                                                                                          SELECT *
                                                                                                                                          FROM   org_id) ) ) ) AS data
                                                                             LEFT JOIN pharmacy_productform
                                                                             ON        data.form_id = pharmacy_productform.id
                                                                             LEFT JOIN pharmacy_productmanufacturingcompany
                                                                             ON        pharmacy_productmanufacturingcompany.id = manufacturing_company_id ) AS part_2
                                                         ON        akey=bkey ) AS data
                                      GROUP BY product_id,
                                               full_name,
                                               organization_id,
                                               form_name,
                                               company ) AS product_info
                   LEFT JOIN
                             (
                                       SELECT    product_id,
                                                 count(stock_io.id) AS used
                                       FROM      (
                                                        SELECT id,
                                                               stock_id
                                                        FROM   pharmacy_stockiolog
                                                        WHERE  organization_id =
                                                               (
                                                                      SELECT *
                                                                      FROM   org_id) ) AS stock_io
                                       LEFT JOIN pharmacy_stock
                                       ON        pharmacy_stock.id = stock_io.stock_id
                                       GROUP BY  pharmacy_stock.product_id ) AS stock_count
                   using     (product_id)
                   LEFT JOIN core_organization
                   ON        product_info.organization_id = core_organization.id) AS data
WHERE    possible_duplicate > 0
ORDER BY full_name,
         used DESC,
         possible_duplicate DESC;'''
        raw_query = raw_query.format(organization_id, Status.ACTIVE, PublishStatus.PRIVATE)
        return list(Product.objects.raw(raw_query))


class ProductList(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsDistributionT1,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission, )
    cache_name = 'list'
    cached_model_name = 'product'
    deleted_cache_model_list = [cached_model_name]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductWithoutStockLiteSerializer
        else:
            return ProductBasicSerializer

    def get_queryset(self):
        stocks = Stock.objects.filter(
            status=Status.ACTIVE,
            organization_id=self.request.user.organization_id,
        ).only(
            'id',
            'product_id',
            'priority',
            'is_ad_enabled',
        )

        select_related = [
            'manufacturing_company',
            'form',
            'subgroup',
            'subgroup__product_group',
            'generic',
            'primary_unit',
            'secondary_unit',
            'category'
        ]
        select_only = [
            'id',
            'alias',
            'created_at',
            'updated_at',
            'name',
            'full_name',
            'is_global',
            'description',
            'trading_price',
            'purchase_price',
            'status',
            'manufacturing_company',
            'form',
            'subgroup',
            'generic',
            'is_salesable',
            'is_service',
            'strength',
            'is_printable',
            'primary_unit',
            'secondary_unit',
            'clone',
            'conversion_factor',
            'minimum_order_quantity',
            'is_published',
            'order_limit_per_day',
            'order_limit_per_day_uttara',
            'order_limit_per_day_mirpur',
            'manufacturing_company',
                'manufacturing_company__id',
                'manufacturing_company__alias',
                'manufacturing_company__name',
                'manufacturing_company__is_global',
                'manufacturing_company__description',
            'form',
                'form__id',
                'form__alias',
                'form__name',
                'form__is_global',
                'form__description',
            'subgroup',
                'subgroup__id',
                'subgroup__alias',
                'subgroup__name',
                'subgroup__is_global',
                'subgroup__description',
                'subgroup__product_group',
            'generic',
                'generic__id',
                'generic__alias',
                'generic__name',
                'generic__is_global',
                'generic__description',
            'primary_unit',
                'primary_unit__id',
                'primary_unit__alias',
                'primary_unit__name',
                'primary_unit__description',
                'primary_unit__created_at',
                'primary_unit__updated_at',
            'secondary_unit',
                'secondary_unit__id',
                'secondary_unit__alias',
                'secondary_unit__name',
                'secondary_unit__description',
                'secondary_unit__created_at',
                'secondary_unit__updated_at',
            'category',
                'category__id',
                'category__alias',
                'category__name',
        ]

        queryset = super(ProductList, self).get_queryset(
            select_related,
            select_only
        ).prefetch_related(
            Prefetch(
                'stock_list',
                queryset=stocks
            )
        )
        queryset = filter_global_product_based_on_settings(self, queryset)
        # queryset = queryset.filter(
        #     global_category__in=self.request.user.organization.get_global_category())
        queryset = sync_queryset(self, queryset)

        return queryset.order_by("-pk")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data
        if isinstance(data, QueryDict):
            data = data.dict()
        base_product = data.get('base_product', None)
        try:
            with transaction.atomic():
                serializer = ProductBasicSerializer(
                    data=request.data,
                    context={'request': request}
                )
                if serializer.is_valid(raise_exception=True):
                    if base_product:
                        serializer.save(
                            entry_by=self.request.user,
                            organization_id=self.request.user.organization_id,
                            clone_id=base_product,
                        )
                        stocks = Stock.objects.filter(
                            organization=self.request.user.organization_id,
                            product=base_product,
                        )

                        for stock in stocks:
                            created_product = Product.objects.only(
                                'id',
                                'full_name',
                                'alias_name',
                            ).get(id=serializer.data['id'])
                            stock.product_id = created_product.id
                            # update stock full name and length cause signal is not updating
                            _product_full_name = ' '.join(
                                filter(
                                    None, [str(created_product.full_name), created_product.alias_name]
                                    )
                                ).lower()
                            stock.product_full_name = _product_full_name
                            stock.product_len = len(_product_full_name)
                            stock.save(update_fields=[
                                'product', 'product_full_name', 'product_len'])

                        create_discarded_item(
                            OrganizationWiseDiscardedProduct,
                            self.request.user,
                            entry_type=DiscardType.EDIT,
                            product_id=serializer.data['id'],
                            parent_id=base_product,
                        )
                    else:
                        serializer.save(
                            entry_by=self.request.user,
                            organization_id=self.request.user.organization_id,
                        )
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)



class ProductStockUnderDemand(ListAPIView):
    permission_classes = (StaffIsAdmin, )
    serializer_class = StockSerializer

    def get_queryset(self):
        return Stock.objects.filter(
            organization=self.request.user.organization_id,
            status=Status.ACTIVE,
            stock__lt=F('demand'),
        ).order_by('pk')


# class ProductSearch(OrganizationAndGlobalWiseSearch):
#     permission_classes = (StaffIsAdmin, )
#     serializer_class = ProductWithStockSerializer
#     model_name = Product

#     def get_queryset(self):
#         return self.serve_queryset(self)


class ProductDetails(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
        StaffIsProcurementManager,
        StaffIsDistributionT1,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission, )
    lookup_field = 'alias'
    deleted_cache_model_list = ['product']

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductWithStockSerializer
        else:
            return ProductBasicSerializer

    def get_queryset(self):
        return Product.objects.filter(
            status=Status.ACTIVE,
        ).select_related(
            'manufacturing_company',
            'form',
            'category',
            'subgroup',
            'subgroup__product_group',
            'generic',
            'primary_unit',
            'secondary_unit',
        ).prefetch_related('stock_list')


class ProductOpeningStockView(ListAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = ProductOpeningStockSerializer
    pagination_class = None

    def get_queryset(self):
        store_points = self.request.query_params.getlist('store_points', None)
        date = self.request.query_params.get('date_0', None)
        groups = self.request.query_params.getlist('groups', None)
        query = Stock().get_active_from_organization(
            self.request.user.organization_id
        ).select_related(
            'store_point',
            'product__manufacturing_company',
            'product__form',
            'product__subgroup__product_group',
            'product__generic',
        ).filter(
            store_point__alias__in=store_points,
            product__status=Status.ACTIVE,
            product__is_service=False,
            stocks_io__status=Status.ACTIVE,
            stocks_io__date__lt=date
        )
        if groups:
            query = query.filter(
                product__subgroup__product_group__alias__in=groups,)
        query = query.annotate(
            sum=Coalesce(Sum(Case(When(
                stocks_io__type=StockIOType.INPUT,
                then=F('stocks_io__quantity')))), 0.00) -
            Coalesce(Sum(Case(When(
                stocks_io__type=StockIOType.OUT,
                then=F('stocks_io__quantity')))), 0.00),
        ).order_by('product')

        return query


# class ProductMedicineSearch(ListAPIView):
#     permission_classes = (StaffIsAdmin, )

#     def get_queryset(self):
#         return Product.objects.filter(
#             Q(name__icontains=self.request.GET.get('keyword'),
#               is_global=PublishStatus.INITIALLY_GLOBAL) |
#             Q(name__icontains=self.request.GET.get('keyword'),
#               is_global=PublishStatus.WAS_PRIVATE_NOW_GLOBAL) |
#             Q(name__icontains=self.request.GET.get('keyword'),
#               organization=self.request.user.organization),
#             subgroup__product_group__name='Medicine',
#             status=Status.ACTIVE
#         ).order_by('pk')

#     serializer_class = ProductWithStockSerializer


class StockList(ListCreateAPICustomView):
    permission_classes = (StaffIsAdmin,)

    def get_queryset(self):
        return Stock.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id,
            product__is_service=False
        ).order_by('pk')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StockSerializer
        else:
            return StockBasicSerializer


class StockSearch(ListAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission, )

    def get_queryset(self):
        return Stock.objects.filter(
            product__name__icontains=self.request.GET.get('keyword'),
            status=Status.ACTIVE,
            product__organization=self.request.user.organization_id
        ).order_by('pk')


class StockDetails(RetrieveUpdateDestroyAPICustomView):
    queryset = Stock.objects.filter(status=Status.ACTIVE)
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )

    permission_classes = (CheckAnyPermission, )

    lookup_field = 'alias'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StockSerializer
        else:
            return StockBasicSerializer


class StockProductList(ListAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsNurse,
        StaffIsSalesman,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission, )

    def get_serializer_class(self):
        requisition = self.request.GET.get('requisition', None)
        transfer_requisition = self.request.GET.get('transfer_requisition', None)
        order = self.request.GET.get('order', None)
        purchase = self.request.GET.get('purchase', None)
        if requisition or order or purchase or transfer_requisition:
            return StockWithProductForRequisitionSerializer
        return StockWithProductUnitSerializer

    lookup_field = 'alias'

    def get_queryset(self):
        store_point_alias = self.kwargs['alias']
        keyword = self.request.GET.get('keyword', '')
        second_store_point = self.request.GET.get(
            'second_store_point', None)
        manufacturing_company = self.request.GET.get('manufacturing_company', None)
        form = self.request.GET.getlist('form')
        is_service = self.request.GET.get('is_service', None)
        product_alias = self.request.GET.get('product', None)
        requisition = self.request.GET.get('requisition', None)
        supplier = self.request.GET.get('person', None)
        order = self.request.GET.get('order', None)
        purchase = self.request.GET.get('purchase', None)
        exact_search = self.request.GET.get('exact_search', None)
        transfer_requisition = self.request.GET.get('transfer_requisition', None)
        is_bar_code = self.request.GET.get('bar_code', None)
        sales_list = self.request.GET.get('sales_list', None)

        # check any letter in keyword is in uppercase
        is_exact_search = True if any(map(str.isupper, str(keyword))) else False

        if requisition or order or purchase or transfer_requisition:
            self.pagination_class = None

        is_stock_out = self.request.GET.get('is_stock_out', None)
        # If auto adjustment is disabled for organization then fetch stocks amount greater than zero
        # is stock out true when request from stock transfer or disbursement
        # and organization auto adjustment disable
        minimum_stock = -1
        if is_stock_out:
            minimum_stock = 0

        try:
            store_point = StorePoint.objects.get(alias=store_point_alias)
        except StorePoint.DoesNotExist:
            store_point = None

        # minimum stock -1 when organization auto adjustment true
        # store point auto adjustment disable then fetch stocks amount greater than zero
        if store_point and is_stock_out and minimum_stock == -1 and \
                not store_point.auto_adjustment:
            minimum_stock = 0

        # skiped_products = self.request.user.organization.get_discarded_product()

        queryset = Stock.objects.select_related(
            'store_point',
            'product',
            'product__subgroup',
            'product__subgroup__product_group',
            'product__form',
            'product__generic',
            'product__manufacturing_company',
            'product__primary_unit',
            'product__secondary_unit',
            'product__category',
            'latest_purchase_unit',
            'latest_sale_unit',
        ).filter(
            organization=self.request.user.organization,
            status=Status.ACTIVE,
            stock__gt=minimum_stock,
            store_point__alias=store_point_alias,
        )

        generated_code = generate_code_with_hex_of_organization_id(
            self.request, keyword)
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
            queryset = queryset.filter(product_full_name__contains=keyword.lower())

        queryset = filter_global_product_based_on_settings(self, queryset)

        if second_store_point:
            second_store_point_queryset = Stock.objects.filter(
                organization=self.request.user.organization,
                status=Status.ACTIVE,
                product_full_name__contains=keyword.lower(),
                store_point__alias__in=second_store_point.split(','),
            ).values_list('product', flat=True)
            queryset = queryset.filter(
                product__in=second_store_point_queryset)

        if product_alias:
            queryset = queryset.filter(product__alias=product_alias)

        if requisition:
            stocks_io = StockIOLog.objects.filter(
                organization=self.request.user.organization,
                status=Status.DRAFT,
                stock__store_point__alias=store_point_alias,
                purchase__alias=requisition
            )
            queryset = queryset.prefetch_related(
                Prefetch('stocks_io', queryset=stocks_io)
            ).filter(
                stocks_io__purchase__alias=requisition
            ).order_by('product').distinct()

        if order:
            stocks_io = StockIOLog.objects.filter(
                organization=self.request.user.organization,
                status=Status.PURCHASE_ORDER,
                stock__store_point__alias=store_point_alias,
                purchase__alias=order
            )
            queryset = queryset.prefetch_related(
                Prefetch('stocks_io', queryset=stocks_io)
            ).filter(
                stocks_io__purchase__alias=order
            ).order_by('product').distinct()

        if purchase:
            stocks_io = StockIOLog.objects.filter(
                organization=self.request.user.organization,
                status=Status.ACTIVE,
                stock__store_point__alias=store_point_alias,
                purchase__alias=purchase
            )
            queryset = queryset.prefetch_related(
                Prefetch('stocks_io', queryset=stocks_io)
            ).filter(
                stocks_io__purchase__alias=purchase
            ).order_by('product').distinct()

        if transfer_requisition:
            stocks_io = StockIOLog.objects.filter(
                organization=self.request.user.organization,
                status=Status.DRAFT,
                stock__store_point__alias=store_point_alias,
                transfer__alias=transfer_requisition
            )
            queryset = queryset.prefetch_related(
                Prefetch('stocks_io', queryset=stocks_io)
            ).filter(
                stocks_io__transfer__alias=transfer_requisition
            ).order_by('product').distinct()

        if supplier:
            queryset = queryset.filter(
                stocks_io__purchase__person_organization_supplier__alias=supplier
            ).order_by('product').distinct()

        if is_service in ['True', 'False']:
            queryset = queryset.filter(product__is_service=is_service)

        if manufacturing_company:
            queryset = queryset.filter(product__manufacturing_company__alias=manufacturing_company)

        if form:
            queryset = queryset.filter(product__form__alias__in=form)

        if exact_search:
            queryset = queryset.filter(product__name__istartswith=exact_search)

        if sales_list:
            sales_list = [int(sale) for sale in sales_list.split(',')]
            queryset = queryset.filter(stocks_io__sales__in=sales_list).distinct()

        queryset = add_log_price_on_stock_queryset(queryset, False)

        if is_exact_search:
            queryset = queryset.order_by(
                'product_len', '-local_count', '-organizationwise_count',
                '-global_count', 'product_full_name'
            )

        elif keyword:
            queryset = queryset.order_by(
                '-local_count', '-organizationwise_count', '-global_count',
                'product_len', 'product_full_name'
            )

        else:
            queryset = queryset.order_by(
                '-local_count', '-organizationwise_count',
                '-global_count',
            )

        return queryset


class SalesAbleStockProductList(ListAPIView):
    from pharmacy.custom_serializer.stock_product_service import SalesableProductOrServiceSerializer

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsSalesman,
        StaffIsNurse,
        StaffIsProcurementOfficer
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = SalesableProductOrServiceSerializer
    lookup_field = 'alias'

    def get_queryset(self):
        keyword = self.request.GET.get('keyword', '')
        store_point_alias = self.kwargs['alias']
        product = self.request.GET.get('product', None)
        purchases = self.request.GET.get('purchases', None)
        buyer = self.request.GET.get('person', None)
        is_bar_code = self.request.GET.get('bar_code', None)

        # check any letter in keyword is in uppercase
        is_exact_search = True if any(map(str.isupper, str(keyword))) else False

        try:
            store_point = StorePoint.objects.get(alias=store_point_alias)
        except StorePoint.DoesNotExist:
            store_point = None

        # If auto adjustment is disabled for organization then fetch stocks amount greater than zero
        minimum_stock = 0
        if self.request.user.organization.organizationsetting.auto_adjustment:
            minimum_stock = -1

        # minimum stock -1 when organization auto adjustment true
        # store point auto adjustment disable then fetch stocks amount greater than zero
        if store_point and minimum_stock == -1 and not store_point.auto_adjustment:
            minimum_stock = 0

        # skiped_products = self.request.user.organization.get_discarded_product()

        queryset = Stock.objects.filter(
            organization=self.request.user.organization,
            status=Status.ACTIVE,
            product__status=Status.ACTIVE,
            product__is_salesable=True,
            product__is_service=False,
            store_point__alias=store_point_alias,
            stock__gt=minimum_stock
        ).select_related(
            'store_point',
            'product',
            'product__manufacturing_company',
            'product__subgroup',
            'product__subgroup__product_group',
            'product__form',
            'product__generic',
            'product__primary_unit',
            'product__secondary_unit',
            'product__category',
            'latest_purchase_unit',
            'latest_sale_unit',
        ).only(
            'id',
            'alias',
            'stock',
            'demand',
            'minimum_stock',
            'rack',
            'tracked',
            'sales_rate',
            'purchase_rate',
            'calculated_price',
            'order_rate',
            'discount_margin',
            'store_point__id',
            'store_point__alias',
            'store_point__name',
            'store_point__phone',
            'store_point__address',
            'store_point__type',
            'store_point__populate_global_product',
            'store_point__auto_adjustment',
            'store_point__created_at',
            'store_point__updated_at',
            'product__id',
            'product__code',
            'product__species',
            'product__alias',
            'product__name',
            'product__strength',
            'product__full_name',
            'product__description',
            'product__trading_price',
            'product__purchase_price',
            'product__status',
            'product__is_salesable',
            'product__is_printable',
            'product__is_service',
            'product__is_global',
            'product__conversion_factor',
            'product__category',

                'product__manufacturing_company__id',
                'product__manufacturing_company__alias',
                'product__manufacturing_company__name',
                'product__manufacturing_company__description',
                'product__manufacturing_company__is_global',

                'product__form__id',
                'product__form__alias',
                'product__form__name',
                'product__form__description',
                'product__form__is_global',

                'product__subgroup__id',
                'product__subgroup__alias',
                'product__subgroup__name',
                'product__subgroup__description',
                'product__subgroup__is_global',

                    'product__subgroup__product_group__id',
                    'product__subgroup__product_group__alias',
                    'product__subgroup__product_group__name',
                    'product__subgroup__product_group__description',
                    'product__subgroup__product_group__is_global',
                    'product__subgroup__product_group__type',

                'product__generic__id',
                'product__generic__alias',
                'product__generic__name',
                'product__generic__description',
                'product__generic__is_global',

                'product__category__id',
                'product__category__alias',
                'product__category__name',
                'product__category__description',
                'product__category__is_global',

                'product__primary_unit__id',
                'product__primary_unit__alias',
                'product__primary_unit__name',
                'product__primary_unit__description',

                'product__secondary_unit__id',
                'product__secondary_unit__alias',
                'product__secondary_unit__name',
                'product__secondary_unit__description',

            'latest_purchase_unit__id',
            'latest_purchase_unit__alias',
            'latest_purchase_unit__name',
            'latest_purchase_unit__description',
            'latest_purchase_unit__created_at',
            'latest_purchase_unit__updated_at',

            'latest_sale_unit__id',
            'latest_sale_unit__alias',
            'latest_sale_unit__name',
            'latest_sale_unit__description',
            'latest_sale_unit__created_at',
            'latest_sale_unit__updated_at',
        )


        generated_code = generate_code_with_hex_of_organization_id(
            self.request, keyword)

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
            queryset = queryset.filter(product__full_name__icontains=keyword)

        queryset = filter_global_product_based_on_settings(self, queryset)

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

        queryset = queryset.annotate(
            log_price=Case(
                When(
                    organization__organizationsetting__price_type=PriceType.PRODUCT_PRICE,
                    then=F('product__trading_price')
                ),
                When(
                    organization__organizationsetting__price_type=PriceType.LATEST_PRICE_AND_PRODUCT_PRICE,
                    sales_rate__lte=0,
                    then=F('product__trading_price')
                ),
                When(
                    organization__organizationsetting__price_type=PriceType.PRODUCT_PRICE_AND_LATEST_PRICE,
                    product__trading_price__gt=0,
                    then=F('product__trading_price')
                ),
                default=F('sales_rate'),
            )
        )

        if is_exact_search:
            queryset = queryset.order_by(
                'product_len', '-local_count', '-organizationwise_count',
                '-global_count', 'product_full_name'
            )

        elif keyword:
            queryset = queryset.order_by(
                '-local_count', '-organizationwise_count', '-global_count',
                'product_len', 'product_full_name'
            )

        else:
            queryset = queryset.order_by(
                '-local_count', '-organizationwise_count',
                '-global_count',
            )

        return queryset


class ProductStockList(ListAPIView):
    available_permission_classes = (
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )
    pagination_class = None

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StockWithStorePointSerializer
        else:
            return StockBasicSerializer

    def get_queryset(self):
        stock_alias = self.kwargs['alias']
        return Stock.objects.filter(
            product__alias=stock_alias,
            status=Status.ACTIVE,
            store_point__status=Status.ACTIVE,
            organization=self.request.user.organization_id
        ).select_related('store_point').order_by('pk')

class StocksPreviousInfo(APIView):
    """Get Stock's Previous Sales qty and current stock qty according to date range"""
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsNurse,
        StaffIsSalesman,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission, )

    def get(self, request, stock_alias):
        start_date = self.request.query_params.get('date_0', None)
        end_date = self.request.query_params.get('date_1', None)
        if not validate_uuid4(stock_alias):
            return Response({})

        queryset = StockIOLog.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id,
            stock__alias=stock_alias,
            sales__isnull=False,
            sales__is_purchase_return=False,
            date__range=[start_date, end_date],
        ).values('stock').annotate(
            sales_qty=Sum(F('quantity')),
            current_stock=F('stock__stock')
        ).order_by()
        if queryset.count() == 0:
            try:
                _current_stock = Stock.objects.values('stock').get(alias=stock_alias)['stock']
            except Stock.DoesNotExist:
                _current_stock = 0
            return Response({
                'sales_qty': 0,
                'current_stock': _current_stock
            })
        return Response(queryset[0])


class StorePointList(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsNurse,
        StaffIsSalesman,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = StorePointSerializer

    def get_queryset(self):
        key_name = create_cache_key_name(self, 'store_point', 'list')
        cached_data_list = cache.get(key_name)
        if cached_data_list and False:
            data = cached_data_list
        else:
            data = StorePoint.objects.filter(
                status=Status.ACTIVE,
                organization=self.request.user.organization_id,
            ).exclude(
                # type=StorePointType.VENDOR_DEFAULT
            ).prefetch_related('product_category').order_by('-id')
            # cache.set(key_name, data)
        data = filter_data_by_user_permitted_store_points(self, data, primary=True)
        data = sync_queryset(self, data)
        return data

    @transaction.atomic
    def create(self, request):
        try:
            product_categories = self.request.data.get('product_category', None)

            serializer = StorePointWithCategorySerializer(
                data=request.data, context={'request': request}
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save(
                    entry_by=self.request.user,
                    organization_id=self.request.user.organization_id
                )

                if product_categories:
                    categories = []
                    for category in product_categories:
                        categories.append({
                            'store_point': serializer.data['id'],
                            'product_category': category,
                        })

                    rest_serializer = StoreProductCategorySerializer(
                        data=categories, many=True)

                    if rest_serializer.is_valid(raise_exception=True):
                        rest_serializer.save(
                            entry_by=self.request.user,
                            organization_id=self.request.user.organization_id
                        )

                # delete cache
                # key_name = create_cache_key_name(self, 'store_point')
                # cache.delete_pattern(key_name)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

# this view is already exists in search app
# class StorePointSearch(ListAPIView):
#     available_permission_classes = (
#         StaffIsAdmin,
#         StaffIsProcurementOfficer,
#         StaffIsNurse,
#         StaffIsSalesman,
#     )
#     permission_classes = (CheckAnyPermission, )

#     serializer_class = StorePointSerializer

#     def get_queryset(self):
#         return StorePoint.objects.filter(
#             name__icontains=self.request.GET.get('keyword'),
#             organization=self.request.user.organization,
#             status=Status.ACTIVE
#         ).order_by('pk')


class StorePointDetails(RetrieveUpdateDestroyAPICustomView):
    queryset = StorePoint.objects.filter(status=Status.ACTIVE)
    permission_classes = (StaffIsAdmin,)
    serializer_class = StorePointWithCategorySerializer
    lookup_field = 'alias'

    def get_queryset(self):
        store_product_category = StoreProductCategory.objects.filter(
            store_point__alias=self.kwargs['alias'],
            organization=self.request.user.organization_id,
            status=Status.ACTIVE,
        ).values_list('product_category__pk', flat=True)

        data = StorePoint.objects.filter(
            status=Status.ACTIVE
        ).prefetch_related(
            Prefetch(
                'product_category',
                queryset=ProductCategory.objects.filter(
                    organization=self.request.user.organization_id,
                    status=Status.ACTIVE,
                    pk__in=store_product_category
                )
            )
        )
        return data

    @transaction.atomic
    def put(self, request, alias):
        added_categories = self.request.data.get('addedCategories', None)
        remove_categories = self.request.data.get('removeCategories', None)
        store_point = StorePoint.objects.get(alias=alias)
        serializer = StorePointWithCategorySerializer(
            store_point, data=request.data, context={'request': request})

        if serializer.is_valid(raise_exception=True):
            serializer.save(updated_by=self.request.user)

            if remove_categories:
                # get the data and inactive it status
                for category in remove_categories:
                    store_category = StoreProductCategory.objects.get(
                        product_category_id=category['id'],
                        store_point_id=serializer.data['id'],
                        organization=self.request.user.organization_id,
                        status=Status.ACTIVE,
                    )
                    store_category.status = Status.INACTIVE
                    store_category.updated_by = self.request.user
                    store_category.save()

            if added_categories:
                categories = []
                for category in added_categories:
                    # get inactive data if exist and update its status
                    try:
                        store_category = StoreProductCategory.objects.get(
                            product_category_id=category['id'],
                            store_point_id=serializer.data['id'],
                            organization=self.request.user.organization_id,
                            status=Status.INACTIVE,
                        )
                        # if store_category:
                        store_category.status = Status.ACTIVE
                        store_category.updated_by = self.request.user
                        store_category.save()

                    # if doesn't exist then create one
                    except StoreProductCategory.DoesNotExist:
                        categories.append({
                            'store_point': serializer.data['id'],
                            'product_category': category['id'],
                        })

                rest_serializer = StoreProductCategorySerializer(
                    data=categories, many=True)

                if rest_serializer.is_valid(raise_exception=True):
                    rest_serializer.save(
                        entry_by=self.request.user,
                        organization_id=self.request.user.organization_id
                    )

            # delete cache
            # key_name = create_cache_key_name(self, 'store_point')
            # cache.delete_pattern(key_name)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_store_point_related_model_data(self, model_name, store_point):
        # get StockIOLogs of related stocks of related store_points
        if model_name.__name__ == 'StockIOLog':
            queryset = model_name.objects.filter(
                status__in=[Status.ACTIVE, Status.DRAFT, Status.PURCHASE_ORDER],
                organization=self.request.user.organization_id,
                stock__store_point=store_point
            )
        # get transactions of related sales of related store_points
        elif model_name.__name__ == 'Transaction':
            queryset = model_name.objects.filter(
                status=Status.ACTIVE,
                organization=self.request.user.organization_id,
                sales__store_point=store_point
            )
        else:
            queryset = model_name.objects.filter(
                status=Status.ACTIVE,
                organization=self.request.user.organization_id,
                store_point=store_point
            )
        return queryset

    def update_store_point_related_model(self, related_object):
        related_object.status = Status.SUSPEND
        related_object.updated_by = self.request.user
        related_object.save()
        return

    @transaction.atomic
    def patch(self, request, alias):
        if not self.request.user.is_superuser:
            error = {'error': 'YOU DO NOT HAVE PERMISSION TO PERFORM THIS ACTION.'}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        store_point = StorePoint.objects.get(alias=alias)
        serializer = StorePointWithCategorySerializer(
            store_point, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save(updated_by=self.request.user)

            # set default store_point empty if the existing one is suspended
            try:
                setting = OrganizationSetting.objects.get(
                    organization=self.request.user.organization_id,
                    default_storepoint=store_point
                )
                setting.default_storepoint = None
                setting.save(update_fields=['default_storepoint'])
            except OrganizationSetting.DoesNotExist:
                pass

            # get all suspend store point related io logs
            io_logs = self.get_store_point_related_model_data(
                StockIOLog, store_point
            )
            # update status of io log, stock status of log
            # and sales, purchase, transfer, adjustment status of every log
            for log in io_logs:
                self.update_store_point_related_model(log)
                self.update_store_point_related_model(log.stock)

                if log.sales:
                    self.update_store_point_related_model(log.sales)

                elif log.purchase:
                    self.update_store_point_related_model(log.purchase)

                elif log.transfer:
                    self.update_store_point_related_model(log.transfer)

                elif log.adjustment:
                    self.update_store_point_related_model(log.adjustment)

            # get related store product categories of suspend store point
            store_product_categories = self.get_store_point_related_model_data(
                StoreProductCategory, store_point
            )
            # update status of those categories
            for category in store_product_categories:
                self.update_store_point_related_model(category)

            # get related employee access store points of suspend store point
            employee_store_points = self.get_store_point_related_model_data(
                EmployeeStorepointAccess, store_point
            )
            # update status of those employee access store point
            for employee_store_point in employee_store_points:
                self.update_store_point_related_model(employee_store_point)

            # get related transactions of suspended store point
            transactions = self.get_store_point_related_model_data(
                Transaction, store_point
            )

            # update status of those transactions
            for _transaction in transactions:
                self.update_store_point_related_model(_transaction)

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PurchaseList(ListCreateAPICustomView):

    available_permission_classes = ()
    filterset_class = PurchaseListFilter

    def get_permissions(self):
        if self.request.method == 'GET':
            self.available_permission_classes = (
                StaffIsProcurementOfficer,
                StaffIsSalesReturn,
                StaffIsAdmin,
            )
        else:
            self.available_permission_classes = (
                StaffIsProcurementOfficer,
                StaffIsSalesReturn,
                StaffIsAdmin,
                StaffIsDistributionT1
            )
        return (CheckAnyPermission(), )

    def populate_data_to_es_index(self, object_):
        from common.helpers import custom_elastic_rebuild
        custom_elastic_rebuild('pharmacy.models.Purchase', {'id': object_.id})

        try:
            transaction_instances = Transaction.objects.filter(
                purchases=object_, status=Status.ACTIVE
            ).values('id', 'accounts')
            for transaction_ in transaction_instances:
                custom_elastic_rebuild(
                    'account.models.Accounts',
                    {'id': transaction_['accounts']}
                )
                custom_elastic_rebuild(
                    'account.models.Transaction',
                    {'id': transaction_['id']}
                )
            if object_.person_organization_supplier:
                custom_elastic_rebuild(
                    'core.models.PersonOrganization',
                    {'id': object_.person_organization_supplier_id}
                )
        except (Transaction.DoesNotExist, PersonOrganization.DoesNotExist):
            pass

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PurchaseListGetSerializer
        else:
            return PurchaseSerializer

    def get_queryset(self):
        show_all = self.request.query_params.get('page_size', None)
        is_sales_return = self.request.query_params.get('is_sales_return', None)

        if show_all == 'showall':
            self.pagination_class = None

        person = self.request.query_params.get('person', None)

        purchase_transaction = TransactionPurchase.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id
        ).select_related(
            'transaction',
        ).only(
            'id',
            'amount',
            'purchase_id',
            'transaction__id',
            'transaction__organization_wise_serial',
        )

        # requisitions = Purchase.objects.filter(
        #     status=Status.DRAFT,
        #     organization=self.request.user.organization,
        # )

        sales_return = Sales.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id
        )

        queryset = Purchase.objects.filter(
            organization=self.request.user.organization_id,
            status=Status.ACTIVE
        ).only(
            'id',
            'alias',
            'vouchar_no',
            'purchase_date',
            'organization_wise_serial',
            'person_organization_supplier',
            'person_organization_supplier__alias',
            'person_organization_supplier__first_name',
            'person_organization_supplier__last_name',
            'person_organization_supplier__company_name',
            'store_point__alias',
            'store_point__name',
            'amount',
            'copied_from',
            'copied_from__alias',
            'copied_from__vouchar_no',
            'transport',
            'grand_total',
            'organization_department',
            'organization_department__alias',
            'organization_department__name',
            'organization_department__description',
            'organization_department__is_global',
            'organization_department__status',
        ).prefetch_related(
            Prefetch('transaction_purchase', queryset=purchase_transaction),
            # Prefetch('requisitions', queryset=requisitions),
            Prefetch('sales_return', queryset=sales_return)
        ).select_related(
            'person_organization_supplier',
            'store_point',
            'copied_from',
            'organization_department'
        ).order_by('-id').distinct()
        queryset = filter_data_by_user_permitted_store_points(self, queryset)

        if person:
            queryset = queryset.filter(
                Q(
                    person_organization_supplier__alias=person
                ) | Q(
                    person_organization_receiver__alias=person
                ) & Q(
                    status=Status.ACTIVE
                )
            )

        if is_sales_return:
            queryset = queryset.filter(
                is_sales_return=True
            )
        else:
            queryset = queryset.filter(
                is_sales_return=False
            )

        return queryset

    @transaction.atomic
    def create(self, request):
        from procurement.models import ProcureGroup
        try:
            requisitions = request.data.get('requisitions', None)
            sales_return = request.data.get('sales_return', None)
            transactions = request.data.pop('transactions', None)
            is_requisition = request.data.pop('is_requisition', False)
            delete_related = request.data.pop('delete_related', False)
            # Frontend is sending procure group id instead of procure id
            related_procurement_id = request.data.pop('related_procurement_id', None)
            copied_from = request.data.get('copied_from', None)

            if requisitions:
                store_point = request.data['store_point']
                for item in request.data['stock_io_logs']:
                    item['stock'] = get_product_store_wise_stock(
                        item['stock'], store_point, Stock
                    )

            serializer = PurchaseSerializer(
                data=request.data,
                context={'request': request}
            )
            if serializer.is_valid(raise_exception=True):
                purchase_object = serializer.save()

                if requisitions:
                    data_list = []
                    for requisition in requisitions:
                        data_list.append({
                            'requisition': requisition,
                            'purchase': serializer.data['id'],
                            'organization': self.request.user.organization_id
                        })

                    serializer_rest = PurchaseRequisitionSerializer(
                        data=data_list, many=True)
                    if serializer_rest.is_valid(raise_exception=True):
                        serializer_rest.save(
                            entry_by=self.request.user,
                        )

                if sales_return:
                    sales_list = []
                    for sales in sales_return:
                        sales_list.append({
                            'sales': sales,
                            'purchase': serializer.data['id'],
                            'organization': self.request.user.organization_id
                        })

                    serializer_rest = SalesReturnSerializer(
                        data=sales_list,
                        many=True
                    )
                    if serializer_rest.is_valid(raise_exception=True):
                        serializer_rest.save(
                            entry_by=self.request.user,
                        )

                if transactions:
                    create_bulk_transaction(self, transactions, {}, serializer.data['id'])

                if not sales_return and not requisitions:
                    update_stock_calculated_price(self, serializer.data['id'])
                    update_stock_related_data_for_purchase_lazy.delay(serializer.data['id'])

                # Populate data to elastic search index
                self.populate_data_to_es_index(purchase_object)

                if is_requisition and copied_from:
                    if delete_related:
                        requisition_instance = Purchase.objects.only('id').get(pk=copied_from)
                        requisition_instance.delete_requisition_related_order_purchase(
                            self.request.user.id,
                            True
                        )
                        if related_procurement_id:
                            try:
                                procure_group_instance = ProcureGroup.objects.only(
                                    'id',
                                    'requisition_id'
                                ).get(pk=related_procurement_id)
                                procure_group_instance.requisition_id = purchase_object.id
                                procure_group_instance.save(update_fields=['requisition_id'])
                            except:
                                pass
                    # purchase_requistions = []
                    # # Find orders of old requisition
                    # orders = PurchaseRequisition.objects.filter(
                    #     status=Status.ACTIVE,
                    #     requisition__id=copied_from
                    # )
                    # # Create instances with new requisition
                    # for order in orders.values_list('purchase', flat=True):
                    #     purchase_requistions.append(
                    #         PurchaseRequisition(
                    #             requisition_id=purchase_object.id,
                    #             purchase_id=order,
                    #             organization_id=self.request.user.organization_id,
                    #             entry_by_id=self.request.user.id,
                    #         )
                    #     )
                    # PurchaseRequisition.objects.bulk_create(purchase_requistions)
                    # # Inactive old instances
                    # orders.update(status=Status.INACTIVE)

                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class StorePointProductStockList(ListAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    serializer_class = StockBasicSerializer

    def get_queryset(self):
        ordered_product = Purchase.objects.filter(
            alias=self.kwargs['order_alias'],
            organization=self.request.user.organization_id,
            is_sales_return=False,
        ).values_list('stock_io_logs__stock__product', flat=True)
        queryset = Stock.objects.filter(
            store_point__alias=self.kwargs['store_alias'],
            product__in=ordered_product
        )
        return queryset


class PurchaseOrderPendingList(ListAPICustomView):

    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = PurchaseListSerializer
    filterset_class = PurchaseOrderListFilter

    def get_queryset(self):
        person = self.request.query_params.get('person', None)
        purchases = Purchase.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id,
            purchase_type=PurchaseType.PURCHASE
        )
        # requisitions = Purchase.objects.filter(
        #     status=Status.DRAFT,
        #     organization=self.request.user.organization,
        # )
        queryset = Purchase.objects.filter(
            organization=self.request.user.organization_id,
            is_sales_return=False,
            status=Status.PURCHASE_ORDER,
            purchase_order_status=PurchaseOrderStatus.PENDING,
        ).select_related(
            'organization',
            'person_organization_supplier',
            'department',
            'receiver',
            'store_point',
            'organization_department',
        ).annotate(
            pending_amount=Cast(F('grand_total') - Coalesce(Sum(Case(When(
                purchases__in=purchases,
                then=F('purchases__grand_total')))), 0.00), FloatField())
        ).order_by('-id').distinct()
        queryset = filter_data_by_user_permitted_store_points(self, queryset)

        if person:
            return queryset.filter(Q(person_organization_supplier__alias=person)\
            | Q(person_organization_receiver__alias=person))
        else:
            return queryset


class PurchaseOrderCompletedList(ListAPICustomView):

    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = PurchaseListSerializer
    filterset_class = PurchaseOrderListFilter

    def get_queryset(self):
        person = self.request.query_params.get('person', None)
        purchases = Purchase.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id,
            purchase_type=PurchaseType.PURCHASE
        )
        queryset = Purchase.objects.filter(
            organization=self.request.user.organization_id,
            is_sales_return=False,
            status=Status.PURCHASE_ORDER,
            purchase_order_status=PurchaseOrderStatus.COMPLETED,
        ).select_related(
            'organization',
            'person_organization_supplier',
            'department',
            'receiver',
            'copied_from',
            'patient_admission',
            'store_point',
            'organization_department'
        ).annotate(
            pending_amount=Cast(F('grand_total') - Coalesce(Sum(Case(When(
                purchases__in=purchases,
                then=F('purchases__grand_total')))), 0.00), FloatField())
        ).order_by('-id').distinct()

        queryset = filter_data_by_user_permitted_store_points(self, queryset)
        if person:
            return queryset.filter(Q(person_organization_supplier__alias=person)\
            | Q(person_organization_receiver__alias=person))
        else:
            return queryset


class PurchaseOrderDiscardedList(ListAPICustomView):

    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = PurchaseListSerializer
    filterset_class = PurchaseOrderListFilter

    def get_queryset(self):
        person = self.request.query_params.get('person', None)
        purchases = Purchase.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id,
            purchase_type=PurchaseType.PURCHASE
        )
        queryset = Purchase.objects.filter(
            organization=self.request.user.organization_id,
            is_sales_return=False,
            status=Status.PURCHASE_ORDER,
            purchase_order_status=PurchaseOrderStatus.DISCARDED,
        ).select_related(
            'organization',
            'person_organization_supplier',
            'department',
            'receiver',
            'copied_from',
            'store_point',
            'organization_department',
        ).annotate(
            pending_amount=Cast(F('grand_total') - Coalesce(Sum(Case(When(
                purchases__in=purchases,
                then=F('purchases__grand_total')))), 0.00), FloatField())
        ).order_by('-id').distinct()

        queryset = filter_data_by_user_permitted_store_points(self, queryset)
        if person:
            return queryset.filter(Q(person_organization_supplier__alias=person)\
            | Q(person_organization_receiver__alias=person))
        else:
            return queryset


class PurchaseOrderRestList(APIView):

    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsSalesman,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )
    # serializer_class = PurchaseOrderRestItemSerializer
    pagination_class = None

    def compare_log_with_stock_io_logs(self, compared_log, stock_io_logs):
        summarize_log = {}
        summarize_qty = 0
        for log in stock_io_logs:
            if compared_log.stock.product == log.stock.product and \
                    compared_log.rate == log.rate:
                if compared_log.secondary_unit_flag:
                    if compared_log.secondary_unit == log.secondary_unit:
                        summarize_qty += compared_log.quantity
                else:
                    summarize_qty += compared_log.quantity
        summarize_log['product'] = compared_log.stock.product.id
        summarize_log['rate'] = compared_log.rate
        summarize_log['unit'] = compared_log.secondary_unit.id \
            if compared_log.secondary_unit_flag \
            else compared_log.primary_unit.id
        summarize_log['stock_io_log'] = compared_log.id
        summarize_log['total_quantity'] = summarize_qty
        return summarize_log

    def get(self, request, order_alias):
        order_alias = self.kwargs['order_alias']
        queryset = Purchase.objects.filter(
            Q(copied_from__alias=order_alias) | Q(alias=order_alias),
            organization=self.request.user.organization_id,
            is_sales_return=False,
        ).select_related(
            'organization',
            'copied_from',
            'person_organization_receiver',
            'person_organization_supplier',
        )

        filter_purchase = StockIOLog.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id
        ).select_related(
            'primary_unit',
            'secondary_unit',
            'stock__product',
            'purchase',
        )

        filter_order = StockIOLog.objects.filter(
            status=Status.PURCHASE_ORDER,
            organization=self.request.user.organization_id
        ).select_related(
            'primary_unit',
            'secondary_unit',
            'stock__product',
            'purchase',
        )

        purchase_queryset = queryset.filter(
            copied_from__alias=order_alias
        ).prefetch_related(
            Prefetch('stock_io_logs', queryset=filter_purchase)
        )

        order_queryset = queryset.filter(
            alias=order_alias
        ).prefetch_related(
            Prefetch('stock_io_logs', queryset=filter_order)
        )

        ordered_logs = []
        for order in order_queryset:
            for log in order.stock_io_logs.all():
                order_log = self.compare_log_with_stock_io_logs(
                    log, order.stock_io_logs.all())
                ordered_logs.append(order_log)

        purchase_logs = []
        for purchase in purchase_queryset:
            for log in purchase.stock_io_logs.all():
                purchase_log = self.compare_log_with_stock_io_logs(
                    log, purchase.stock_io_logs.all())
                purchase_logs.append(purchase_log)

        for index, order in enumerate(ordered_logs):
            recieve_qty = 0
            for purchase in purchase_logs:
                if order['product'] == purchase['product'] and \
                        order['rate'] == purchase['rate'] and \
                        order['unit'] == purchase['unit']:
                    recieve_qty += purchase['total_quantity']
            ordered_logs[index]['received'] = recieve_qty
            ordered_logs[index]['rest_item'] = \
                order['total_quantity'] - recieve_qty
            ordered_logs[index]['ordered'] = order['total_quantity']
            ordered_logs[index].pop('total_quantity', None)

        return Response(ordered_logs)


class PurchaseOrderReport(ListAPICustomView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = PurchaseOrderReportSerializer
    filterset_class = PurchaseOrderListFilter

    def get_queryset(self):
        show_all = self.request.query_params.get('page_size', None)
        if show_all == 'showall':
            self.pagination_class = None
        person = self.request.query_params.get('person', None)
        purchases = Purchase.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id,
            purchase_type=PurchaseType.PURCHASE
        )
        transaction_purchase = TransactionPurchase.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id
        )
        queryset = Purchase.objects.filter(
            status=Status.PURCHASE_ORDER,
            organization=self.request.user.organization_id,
            purchase_type=PurchaseType.ORDER,
            is_sales_return=False,
            purchase_order_status__in=[
                PurchaseOrderStatus.PENDING,
                PurchaseOrderStatus.COMPLETED,
                PurchaseOrderStatus.DISCARDED
            ]
        ).prefetch_related(
            Prefetch('purchases', queryset=purchases.prefetch_related(
                Prefetch('transaction_purchase', queryset=transaction_purchase)
            ))
        ).select_related(
            'organization',
            'supplier',
            'department',
            'receiver',
            'copied_from',
            'patient_admission',
            'receiver__designation',
            'receiver__designation__department',
            'store_point',
        ).annotate(
            pending_amount=F('grand_total') - Coalesce(Sum(Case(When(
                purchases__in=purchases,
                then=F('purchases__grand_total')))), 0.00)).order_by('-id').distinct()
        if person:
            return queryset.filter(Q(person_organization_supplier__alias=person)\
            | Q(person_organization_receiver__alias=person))
        else:
            return queryset


class PurchaseRequisitionList(ListAPICustomView):

    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsNurse,
        StaffIsAdmin,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission, )
    filterset_class = PurchaseRequisitionFilter
    pagination_class = CachedCountPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PurchaseRequisitionListGetSerializer
        else:
            return PurchaseSerializer

    def get_queryset(self):
        queryset = Purchase.objects.filter(
            organization=self.request.user.organization_id,
            is_sales_return=False,
            status=Status.DRAFT
        ).select_related(
            'person_organization_receiver',
            'person_organization_supplier',
            'person_organization_receiver__person',
            'person_organization_receiver__designation',
            'person_organization_receiver__designation__department',
            'store_point',
            'department',
        ).order_by('-id').distinct()
        return queryset


class PurchaseDetails(RetrieveUpdateDestroyAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
        StaffIsTelemarketer,
        StaffIsSalesCoordinator,
        StaffIsDeliveryHub,
        StaffIsDistributionT2,
        StaffIsDistributionT3,
        StaffIsFrontDeskProductReturn,
        StaffIsSalesManager
    )
    permission_classes = (CheckAnyPermission, )

    lookup_field = 'alias'

    def get_queryset(self):
        return Purchase.objects.filter().prefetch_related(
            Prefetch(
                'stock_io_logs',
                queryset=StockIOLog.objects.filter(
                    Q(status=Status.ACTIVE) | Q(status=Status.PURCHASE_ORDER)
                ).order_by('-id')
            ),
            Prefetch(
                'requisitions',
                queryset=Purchase.objects.filter(status=Status.DRAFT),
            ),
            Prefetch(
                'copied_from__requisitions',
                queryset=Purchase.objects.filter(status=Status.DRAFT),
            )
        )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PurchaseDetailsSerializer
        return PurchaseBasicSerializer

    def validate_grand_total(self, purchase):
        """
        value of 'calculated_grand_total' should be same as value of 'grand_total' (payload)
        """
        if 'grand_total' not in self.request.data:
            # Only delete request doesn't have `grand_total`.
            # That means nothing to validate.
            return

        purchase.refresh_from_db()
        io_log_queryset = purchase.stock_io_logs.filter(
            Q(status=Status.ACTIVE) | Q(status=Status.PURCHASE_ORDER)
        ).values(
            'rate',
            'quantity',
            'discount_total',
            'vat_total',
            'tax_total',
            'conversion_factor',
            'secondary_unit_flag'
        )

        sub_total = 0
        # calculate subtotal, vat, discount based on all individual IOLog
        for item in io_log_queryset:
            qty = item.get('quantity', 0) / item.get('conversion_factor', 1) \
                if item.get('secondary_unit_flag') \
                else item.get('quantity', 0)

            sub_total += (item.get('rate', 0) * qty)
            sub_total += item.get('vat_total', 0)
            sub_total += item.get('tax_total', 0)
            sub_total -= item.get('discount_total', 0)

        # check if calculated total is same as grand_total
        re_validate_grand_total(
            grand_total=self.request.data.get('grand_total', 0),
            calculated_grand_total=sub_total + purchase.round_discount
        )

    @transaction.atomic
    def perform_update(self, serializer, extra_fields=None):
        new_io_logs = self.request.data.get('stock_io_logs', None)
        update_io_logs = self.request.data.get('update_io_logs', None)
        removed_io_logs = self.request.data.get('removed_io_logs', None)
        supplier = self.request.data.get('person_organization_supplier', None)

        self.create_data = {}
        if hasattr(serializer.Meta.model, 'updated_by'):
            self.create_data['updated_by'] = self.request.user

        if supplier:
            self.create_data['supplier'] = PersonOrganization.objects.get(
                pk=supplier
            ).person

        if extra_fields is not None:
            self.add_extra_fields(extra_fields)

        try:
            purchase = Purchase.objects.get(alias=self.kwargs['alias'])
        except Purchase.DoesNotExist as exception:
            content = {'error': '{}'.format(exception)}
            return Response(
                content, status=status.HTTP_400_BAD_REQUEST)

        # saving grand_total manually as it is read_only in serializer
        try:
            with transaction.atomic():
                if hasattr(serializer.Meta.model, 'grand_total'):
                    grand_total = self.request.data.get('grand_total', None)
                    if grand_total is not None:
                        if float(purchase.grand_total) != float(grand_total):
                            self.create_data['grand_total'] = grand_total
                serializer.save(**self.create_data)
        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            raise APIException(content)

        try:
            with transaction.atomic():
                # create new io-logs with the existing purchase / order
                if purchase and new_io_logs:
                    # create stock io logs in reverse order
                    for item in reversed(new_io_logs):
                        primary_unit = item.get('primary_unit')
                        secondary_unit = item.get('secondary_unit')
                        expire_date = datetime.datetime.strptime(
                            item.get('expire_date'), '%Y-%m-%d').date()

                        try:
                            stock = Stock.objects.get(pk=item['stock'])
                        except Stock.DoesNotExist as exception:
                            content = {'error': '{}'.format(exception)}
                            return Response(
                                content, status=status.HTTP_400_BAD_REQUEST)
                        del item['stock']
                        del item['primary_unit']
                        del item['secondary_unit']
                        del item['expire_date']
                        StockIOLog.objects.create(
                            organization_id=self.request.user.organization_id,
                            entry_by=self.request.user,
                            status=purchase.status,
                            purchase=purchase,
                            type=StockIOType.INPUT,
                            primary_unit_id=primary_unit,
                            secondary_unit_id=secondary_unit,
                            date=purchase.purchase_date,
                            stock=stock,
                            expire_date=expire_date,
                            **item
                        )
            # update related stock-io-log
            if purchase and update_io_logs:
                for item in update_io_logs:
                    io_log = StockIOLog.objects.get(pk=item['io_log'])
                    io_log.quantity = item['quantity']
                    if item.get('secondary_unit'):
                        io_log.secondary_unit_id = item['secondary_unit']
                    io_log.secondary_unit_flag = item['secondary_unit_flag']
                    io_log.conversion_factor = item['conversion_factor']
                    io_log.rate = item['rate']
                    io_log.batch = item['batch']
                    io_log.vat_rate = item['vat_rate']
                    io_log.vat_total = item['vat_total']
                    io_log.discount_rate = item['discount_rate']
                    io_log.discount_total = item['discount_total']
                    io_log.expire_date = datetime.datetime.strptime(
                            item.get('expire_date'), '%Y-%m-%d').date() if item.get('expire_date') else None
                    io_log.save(
                        update_fields=[
                            'quantity', 'secondary_unit', 'rate', 'batch',
                            'secondary_unit_flag', 'expire_date',
                            'discount_rate', 'vat_rate',
                            'discount_total', 'vat_total',
                            'conversion_factor'
                        ]
                    )

            # set status as inactive in stock-io log which is remove from a purchase / order
            if purchase and removed_io_logs:
                for item in removed_io_logs:
                    io_log = StockIOLog.objects.get(pk=item)
                    io_log.status = Status.INACTIVE
                    io_log.save(update_fields=['status'])

            # update calculated price of a product
            if purchase.status == Status.ACTIVE:
                update_stock_calculated_price(self, purchase.id)

            self.validate_grand_total(purchase)
            update_stock_related_data_for_purchase_lazy.delay(purchase.id)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            raise APIException(content)


class PurchaseRequisitionDetails(RetrieveUpdateDestroyAPIView):

    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
        StaffIsDistributionT1,
    )
    permission_classes = (CheckAnyPermission, )

    lookup_field = 'alias'

    def get_queryset(self):
        stock_io_log_qs = StockIOLog.objects.filter(
            status=Status.DRAFT
        ).select_related(
            "primary_unit",
            "secondary_unit",
            "stock__store_point",
            "stock__product__category",
            "stock__product__compartment",
            "stock__product__generic",
            "stock__product__form",
            "stock__product__manufacturing_company",
            "stock__product__subgroup",
            "stock__product__subgroup__product_group",
            "stock__product__primary_unit",
            "stock__product__secondary_unit",
        )
        return Purchase.objects.filter(is_sales_return=False).prefetch_related(
            Prefetch(
                'stock_io_logs',
                queryset=stock_io_log_qs
            )
        )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PurchaseDetailsSerializer
        else:
            return PurchaseSerializer

    @transaction.atomic
    def perform_update(self, serializer):
        delete_related = self.request.data.pop('delete_related', False)
        if delete_related:
            requisition_instance = self.get_object()
            requisition_instance.delete_requisition_related_order_purchase(
                self.request.user.id,
            )
        return super().perform_update(serializer)


class SalesReturnList(PurchaseList):
    def get_queryset(self):
        return Purchase.objects.filter(
            organization=self.request.user.organization_id,
            is_sales_return=True,
            status=Status.ACTIVE
        ).order_by('pk')


class SalesReturnDetails(PurchaseDetails):
    queryset = Purchase.objects.filter(
        is_sales_return=True,
        status=Status.ACTIVE)


class StockIOList(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = StockIOLogSerializer

    def get_queryset(self):
        return StockIOLog.objects.filter(
            organization=self.request.user.organization_id,
            status=Status.ACTIVE
        ).order_by('pk')


class StockIOListStorePointBatchWise(ListAPIView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsNurse,
        StaffIsSalesman,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = StockIOLogBatchWiseSerializer
    pagination_class = None

    def get_queryset(self):
        store_point_id = self.kwargs['store']
        # TO DO: FIX THIS IN ORM

        raw_query = '''
        SELECT 1                              AS id,
            stock_id,
            batch,
            Min(expire_date),
            Sum(stock_in) - Sum(stock_out) AS qty
        FROM   (SELECT stock_id,
                    batch,
                    Min(expire_date) AS expire_date,
                    Sum(quantity)    AS stock_in,
                    0                AS stock_out
                FROM   pharmacy_stockiolog sio
                    LEFT JOIN pharmacy_stock s
                            ON sio.stock_id = s.id
                WHERE  store_point_id = {}
                    AND type = 0
                GROUP  BY stock_id,
                        batch
                UNION
                SELECT stock_id,
                    batch,
                    '2099-12-12'  AS expire_date,
                    0             AS stock_in,
                    Sum(quantity) AS stock_out
                FROM   pharmacy_stockiolog sio
                    LEFT JOIN pharmacy_stock s
                            ON sio.stock_id = s.id
                WHERE  store_point_id = {}
                    AND type = 1
                GROUP  BY stock_id,
                        batch) AS a
        GROUP  BY stock_id,
                batch '''
        raw_query = raw_query.format(store_point_id, store_point_id)
        return StockIOLog.objects.raw(raw_query)


class StockIOListStorePointProductBatchWise(ListAPIView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsNurse,
        StaffIsSalesman,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission, )

    def get_serializer_class(self):
        if self.request.query_params.get('allow_stock', True) == 'false':
            return WithoutStockIOLogBatchWiseSerializer
        return StockIOLogBatchWiseSerializer

    pagination_class = None

    def get_queryset(self):
        store_point_id = self.kwargs['store']
        product_id = self.kwargs['product']
        try:
            return Stock.objects.get(
                store_point__id=store_point_id,
                product__id=product_id,
                status=Status.ACTIVE
            ).get_batch_info()
        except Stock.DoesNotExist:
            return None

class StockIOListStorePointProductBatchDateWise(ListAPIView):

    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = StockIOLogBatchWiseDateSerializer
    pagination_class = None

    def get_queryset(self):
        store_point_id = self.kwargs['store']
        product_id = self.kwargs['product']
        date = "{}-{}-{}".format(
            self.kwargs['year'], self.kwargs['month'], self.kwargs['day'])

        # TO DO: FIX THIS IN ORM

        raw_query = '''
        SELECT 1                              AS id,
            stock_id,
            batch,
            Min(expire_date),
            Sum(stock_in) - Sum(stock_out) AS qty
        FROM   (SELECT stock_id,
                    batch,
                    Min(expire_date) AS expire_date,
                    Sum(quantity)    AS stock_in,
                    0                AS stock_out
                FROM   pharmacy_stockiolog sio
                    LEFT JOIN pharmacy_stock s
                            ON sio.stock_id = s.id
                WHERE  store_point_id = {}
                    AND product_id = {}
                    AND date <= '{}'
                    AND type = 0
                GROUP  BY stock_id,
                        batch
                UNION
                SELECT stock_id,
                    batch,
                    '2099-12-12'  AS expire_date,
                    0             AS stock_in,
                    Sum(quantity) AS stock_out
                FROM   pharmacy_stockiolog sio
                    LEFT JOIN pharmacy_stock s
                            ON sio.stock_id = s.id
                WHERE  store_point_id = {}
                    AND product_id = {}
                    AND date <= '{}'
                    AND type = 1
                GROUP  BY stock_id,
                        batch) AS a
        GROUP  BY stock_id,
                batch '''
        raw_query = raw_query.format(
            store_point_id, product_id, date, store_point_id, product_id, date)

        return StockIOLog.objects.raw(raw_query)


class StockIOListProductBatchWise(ListAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = StockIOLogSerializer
    pagination_class = None

    def get_queryset(self):
        product_id = self.kwargs['product']

        raw_query = '''
        SELECT 1                              AS id,
            stock_id,
            batch,
            Min(expire_date),
            Sum(stock_in) - Sum(stock_out) AS qty
        FROM   (SELECT stock_id,
                    batch,
                    Min(expire_date) AS expire_date,
                    Sum(quantity)    AS stock_in,
                    0                AS stock_out
                FROM   pharmacy_stockiolog sio
                    LEFT JOIN pharmacy_stock s
                            ON sio.stock_id = s.id
                WHERE product_id = {}
                    AND type = 0
                    AND sio.status = 0
                GROUP  BY stock_id,
                        batch
                UNION
                SELECT stock_id,
                    batch,
                    '2099-12-12'  AS expire_date,
                    0             AS stock_in,
                    Sum(quantity) AS stock_out
                FROM   pharmacy_stockiolog sio
                    LEFT JOIN pharmacy_stock s
                            ON sio.stock_id = s.id
                WHERE product_id = {}
                    AND type = 1
                    AND sio.status = 0
                GROUP  BY stock_id,
                        batch) AS a
        GROUP  BY stock_id,
                batch '''
        raw_query = raw_query.format(
            product_id, product_id)
        return StockIOLog.objects.raw(raw_query)


class StockIOListByStore(ListAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = StockIOLogSerializer

    def get_queryset(self):
        from_date = self.request.GET.get('from')
        start_date = datetime.datetime.strptime(from_date, '%d-%m-%Y').date()
        to_date = self.request.GET.get('to')
        end_date = datetime.datetime.strptime(to_date, '%d-%m-%Y').date()
        return StockIOLog.objects.filter(
            stock__store_point__alias=self.kwargs['alias'],
            stock__product__alias=self.kwargs['product'],
            organization=self.request.user.organization_id,
            status=Status.ACTIVE,
            date__range=[start_date, end_date]
        ).order_by('pk')

    def list(self, request, *args, **kwargs):
        try:
            from_date = self.request.GET.get('from')
            to_date = self.request.GET.get('to')
            if from_date is None or to_date is None:
                raise ValueError
            # start_date = datetime.datetime.strptime(
            #     from_date, '%d-%m-%Y').date()
            # end_date = datetime.datetime.strptime(to_date, '%d-%m-%Y').date()

            queryset = self.get_queryset()
            serializer = StockIOLogSerializer(queryset, many=True)
            return Response({'count': queryset.count(),
                             'results': serializer.data},
                            status=status.HTTP_200_OK)

        except ValueError:
            content = {'error': 'Incorrect data format, should be DD-MM-YYYY'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class StockIOBulkCreate(CreateAPIView):

    available_permission_classes = (
        StaffIsAdmin,
        StaffIsNurse,
        StaffIsSalesman,
        StaffIsProcurementOfficer,
    )

    permission_classes = (CheckAnyPermission, )

    serializer_class = StockIOLogSerializer

    def post(self, request, *args, **kwargs):
        stock_io_logs = request.data['stock_io_logs']
        try:
            serializer = StockIOLogSerializer(
                data=stock_io_logs, many=True, context={'request': request})
            if serializer.is_valid(raise_exception=True):
                serializer.save(organization_id=self.request.user.organization_id)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class StockIODetails(RetrieveUpdateDestroyAPICustomView):
    queryset = StockIOLog.objects.filter(status=Status.ACTIVE)
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = StockIOLogSerializer
    lookup_field = 'alias'


class BatchSearch(ListAPIView):
    serializer_class = StockIOLogSerializer
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )

    def get_queryset(self):
        stock_alias = self.kwargs.get('alias')
        return StockIOLog.objects.filter(
            stock__alias=stock_alias,
            type=StockIOType.INPUT,
            batch__icontains=self.request.GET.get('keyword'),
            status=Status.ACTIVE
        ).order_by('pk')


class AllBatchSearch(ListAPIView):
    serializer_class = StockIOLogSerializer
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )

    def get_queryset(self):
        return StockIOLog.objects.filter(
            batch__icontains=self.request.GET.get('keyword'),
            status=Status.ACTIVE
        ).order_by('pk')


class StockTransferList(ListCreateAPICustomView):
    filterset_class = StockTransferFilter
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsNurse,
        StaffIsAdmin,
        StaffIsSalesman,
    )
    permission_classes = (CheckAnyPermission, )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StockTransferLiteSerializer
        else:
            return StockTransferSerializer

    def get_queryset(self):
        person = self.request.query_params.get('person', None)
        organization_id = str(format(self.request.user.organization_id, '04d'))
        key_stock_transfer_list = 'stock_transfer_list_{}'.format(organization_id)
        cached_list = cache.get(key_stock_transfer_list)

        if cached_list and False:
            data = cached_list
            if person:
                data = cached_list.filter(
                    Q(person_organization_by__alias=person) |
                    Q(person_organization_received_by__alias=person)
                ).select_related(
                    'transfer_from',
                    'transfer_to',
                    'person_organization_by__person',
                ).order_by('-id')
        else:
            data = StockTransfer().get_active_from_organization(
                self.request.user.organization_id
                ).select_related(
                    'transfer_from',
                    'transfer_to',
                    'person_organization_by__person',
                ).order_by('-id')
            # cache.set(key_stock_transfer_list, data)
            data = filter_data_by_user_permitted_store_points(
                self, data, 'transfer_from', 'transfer_to')
            if person:
                data = data.filter(
                    Q(person_organization_by__alias=person) |
                    Q(person_organization_received_by__alias=person)
                )
        return data

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        sid = transaction.savepoint()
        try:
            requisitions = request.data.get('requisitions', None)
            serializer = StockTransferSerializer(
                data=request.data,
                context={'request': request}
            )

            if serializer.is_valid(raise_exception=True):
                serializer.save()
                # save requisition entries to StockTranferRequisition
                if requisitions:
                    data_list = []
                    for requisition in requisitions:
                        data_list.append({
                            'requisition': requisition,
                            'stock_transfer': serializer.data['id'],
                            'organization': self.request.user.organization_id
                        })

                    serializer_req = StockTransferRequisitionSerializer(
                        data=data_list, many=True)
                    if serializer_req.is_valid(raise_exception=True):
                        serializer_req.save(
                            entry_by=self.request.user,
                        )
                # organization_id = str(format(self.request.user.organization_id, '04d'))
                # key_stock_transfer_list = 'stock_transfer_list_{}*'.format(organization_id)
                # cache.delete_pattern(key_stock_transfer_list)
                # transaction.savepoint_commit(sid)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )

        except IntegrityError as exception:
            transaction.savepoint_rollback(sid)
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class StockTransferRequisitionList(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsNurse,
        StaffIsAdmin,
        StaffIsSalesman,
    )
    permission_classes = (CheckAnyPermission, )
    filterset_class = StockTransferRequisitionFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StockTransferLiteSerializer
        else:
            return StockTransferSerializer

    def get_queryset(self):
        queryset = StockTransfer.objects.filter(
            organization=self.request.user.organization_id,
            status=Status.DRAFT
        ).select_related(
            'transfer_from',
            'transfer_to',
            'by',
            'received_by'
        ).order_by('-id')
        queryset = filter_data_by_user_permitted_store_points(
            self, queryset, 'transfer_from', 'transfer_to')
        return queryset


class StockTransferDetails(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = StockTransferDetailsSerializer
    lookup_field = 'alias'

    def get_queryset(self):
        return StockTransfer.objects.filter(
            ~Q(status=Status.INACTIVE),
            organization=self.request.user.organization_id,
        ).prefetch_related(
            Prefetch(
                'stock_io_logs',
                queryset=StockIOLog.objects.filter(~Q(status=Status.INACTIVE))
            )
        )

    @transaction.atomic
    def perform_update(self, serializer):
        try:
            with transaction.atomic():
                if serializer.is_valid(raise_exception=True):
                    serializer.save(updated_by=self.request.user)
        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            raise APIException(content)


# class StockIOList(ListCreateAPIView):
#     permission_classes = (IsOwnerAndAdmin, )
#     serializer_class = StockIOLogSerializer
#
#     def get_queryset(self):
#         return StockIOLog.objects.filter(
#             organization=self.request.user.organization,
#             status=Status.ACTIVE
#         ).order_by('pk')
#
#     def perform_create(self, serializer):
#         serializer.save(organization=self.request.user.organization)
#
#
# class StockIODetails(RetrieveUpdateDestroyAPIView):
#     queryset = StockIOLog.objects.filter(status=Status.ACTIVE)
#     permission_classes = (IsOwnerAndAdmin, )
#     serializer_class = StockIOLogSerializer
#
#     def perform_update(self, serializer):
#         serializer.save(organization=self.request.user.organization)


class StockIOExpiredList(ListAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = StockIOLogBatchWiseSerializer
    pagination_class = None

    def get_queryset(self):
        id = self.kwargs['id']
        date = "{}-{}-{}".format(
            self.kwargs['year'], self.kwargs['month'], self.kwargs['day'])

        # TO DO: FIX THIS IN ORM

        raw_query = '''
        SELECT * FROM (
        SELECT 1                              AS id,
            stock_id,
            batch,
            Min(expire_date) as expire_date,
            Sum(stock_in) - Sum(stock_out) AS qty
        FROM   (SELECT stock_id,
                    batch,
                    Min(expire_date) AS expire_date,
                    Sum(quantity)    AS stock_in,
                    0                AS stock_out
                FROM   pharmacy_stockiolog sio
                    LEFT JOIN pharmacy_stock s
                            ON sio.stock_id = s.id
                WHERE  store_point_id = {}
                    AND type = 0 AND expire_date <= '{}'
                GROUP  BY stock_id,
                        batch
                UNION
                SELECT stock_id,
                    batch,
                    '2099-12-12'  AS expire_date,
                    0             AS stock_in,
                    Sum(quantity) AS stock_out
                FROM   pharmacy_stockiolog sio
                    LEFT JOIN pharmacy_stock s
                            ON sio.stock_id = s.id
                WHERE  store_point_id = {}
                    AND type = 1
                GROUP  BY stock_id,
                        batch) AS a

        GROUP  BY stock_id,
                batch) AS a WHERE a.expire_date <= '{}' AND a.qty > 0'''

        raw_query = raw_query.format(id, date, id, date)
        return StockIOLog.objects.raw(raw_query)


class StockIOReport(ListAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = StockIOReportSerializer
    pagination_class = None

    def get_queryset(self):
        date_0 = self.request.query_params.get('date_0', None)
        date_1 = self.request.query_params.get('date_1', None)
        store_point = self.request.query_params.get('store_point', None)
        product = self.request.query_params.get('product', None)
        batch = self.request.query_params.get('batch', None)
        values = {
            'type': 0,
            'date__gte': date_0,
            'date__lte': date_1,
            'batch': batch,
            'stock__product__alias': product,
            'stock__store_point': store_point
        }
        arguments = {}
        for key, value in values.items():
            if value:
                arguments[key] = value
        queryset = StockIOLog.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id,
            stock__product__is_service=False,
            **arguments
        ).select_related('adjustment').values(
            'date',
            'batch',
            'sales__alias',
            'sales__is_purchase_return',
            'purchase__alias',
            'purchase__is_sales_return',
            'adjustment__alias',
            'transfer__alias',
            'adjustment__is_product_disbrustment'
        ).annotate(
            product_in=Coalesce(Sum(Case(When(
                type=StockIOType.INPUT,
                then=F('quantity')))), 0.00),
            product_out=Coalesce(Sum(Case(When(
                type=StockIOType.OUT,
                then=F('quantity')))), 0.00),
            row_total=Coalesce(Sum(Case(When(
                type=StockIOType.INPUT,
                then=F('quantity')))), 0.00) -
            Coalesce(Sum(Case(When(
                type=StockIOType.OUT,
                then=F('quantity')))), 0.00),
        ).order_by('date', 'updated_at')
        return queryset

    def list(self, request):
        opening_date = self.request.query_params.get('date_0', None)
        store_point = self.request.query_params.get('store_point', None)
        product = self.request.query_params.get('product', None)
        batch = self.request.query_params.get('batch', None)
        values = {
            'type': 0,
            'date__lt': opening_date,
            'batch': batch,
            'stock__product__alias': product,
            'stock__store_point': store_point,
        }
        arguments = {}
        for key, value in values.items():
            if value:
                arguments[key] = value
        opening_stock = StockIOLog.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id,
            **arguments
        ).aggregate(
            opening_stock=Coalesce(Sum(Case(When(type=StockIOType.INPUT,
                                                 then=F('quantity')))), 0.00) -
            Coalesce(Sum(Case(When(type=StockIOType.OUT,
                                   then=F('quantity')))), 0.00)
        )
        serializer = StockIOReportSerializer(self.get_queryset(), many=True)
        stock = opening_stock['opening_stock']
        for i in range(len(serializer.data)):
            serializer.data[i]['stock'] = serializer.data[i]['stock'] + \
                int(stock)
            stock = serializer.data[i]['stock']
        return Response(serializer.data)


class StockReport(ListAPICustomView):

    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsNurse,
        StaffIsAdmin,
        StaffIsSalesman,
    )
    permission_classes = (CheckAnyPermission, )

    def get_serializer_class(self):
        stock_demand = self.request.query_params.get('stock_demand', None)
        profit_date_0 = self.request.query_params.get('profit_date_0', None)
        profit_date_1 = self.request.query_params.get('profit_date_1', None)
        profit_report_summary = self.request.query_params.get('profit_report_summary', None)
        batch = self.request.query_params.get('batch', None)
        if stock_demand == 'true':
            return StockReportDemandSerializer.List
        if profit_date_0 and profit_date_1 and not profit_report_summary:
            return StockProfitReportSerializer

        if profit_date_0 and profit_date_1 and profit_report_summary:
            return StockProfitReportSummarySerializer
        if batch:
            return StockReportBatchWiseSerializer
        return StockReportSerializer

    def get_product_under_demand_stock_report(self):
        values = {
            'organization': self.request.user.organization_id,
            'status': Status.ACTIVE,
            'product__generic__alias': self.request.query_params.get('generic', None),
            'product__form__alias': self.request.query_params.get('product_form', None),
            'product__subgroup__product_group__alias': self.request.query_params.get('group', None),
            'store_point__alias': self.request.query_params.get('store_point', None),
            'product__manufacturing_company__alias': self.request.query_params.get('company', None),
            'product__is_service': False,
        }
        products = self.request.query_params.get('product', None)
        if products:
            values['product__alias__in'] = products.split(',')

        arguments = {key: value for key, value in values.items()\
            if value or value == 0}

        io_logs = StockIOLog.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id,
            type=StockIOType.INPUT,
        )
        queryset = Stock.objects.filter(
            minimum_stock__gt=0,
            stock__lte=F('minimum_stock'),
            **arguments
        ).select_related(
            'store_point',
            'product',
            'product__manufacturing_company',
            'product__generic',
            'product__subgroup',
            'product__form',
            'product__subgroup__product_group',
        ).order_by('store_point__id', 'product_full_name', 'id').prefetch_related(
            Prefetch('stocks_io', queryset=io_logs)
        )
        return queryset

    def get_queryset(self):
        is_distributor = self.request.user.organization.type == OrganizationType.DISTRIBUTOR
        profit_date_0 = self.request.query_params.get('profit_date_0', None)
        profit_date_1 = self.request.query_params.get('profit_date_1', None)
        ignore_zero_purchase = self.request.query_params.get('ignore_zero_purchase_price', 'false')
        profit_report_summary = self.request.query_params.get('profit_report_summary', None)
        values = {
            'date__gte': self.request.query_params.get('date_0', None),
            'date__lte': self.request.query_params.get('date_1', None),
            'expire_date__gte': self.request.query_params.get('expire_date_0', None),
            'expire_date__lte': self.request.query_params.get('expire_date_1', None),
            'stock__product__generic__alias': self.request.query_params.get('generic', None),
            'stock__product__form__alias': self.request.query_params.get('product_form', None),
            'stock__product__subgroup__product_group__alias': \
                self.request.query_params.get('group', None),
            'stock__product__manufacturing_company__alias': self.request.query_params.get(
                'company', None),
            'organization': self.request.user.organization_id,
            'status': Status.ACTIVE,
            'stock__product__is_service': False
        }
        if is_distributor:
            values['status__in'] = values.pop('status')
            values['status__in'] = [Status.ACTIVE, Status.DRAFT]
        store_points = self.request.query_params.get('store_point', None)
        if store_points:
            values['stock__store_point__alias__in'] = store_points.split(',')
        # values['stock__store_point__alias'] = self.request.query_params.get(
        #     'store_point', None)

        # if profit report filter as date_range is selected
        products = self.request.query_params.get('product', None)
        if products:
            values['stock__product__alias__in'] = products.split(',')
        if profit_date_0 and profit_date_1:
            values['date__gte'] = profit_date_0
            values['date__lte'] = profit_date_1
            values.pop('expire_date__gte', None)
            values.pop('expire_date__lte', None)
            values.pop('stock__product__is_service', None)

        arguments = {key: value for key, value in values.items()\
            if value or value == 0}

        queryset = StockIOLog.objects.filter(
            **arguments
        ).select_related(
            'stock',
            'stock__store_point',
            'stock__product',
            'stock__product__manufacturing_company',
            'stock__product__generic',
            'stock__product__subgroup',
            'stock__product__form',
            'stock__product__subgroup__product_group',
        ).order_by('stock__store_point__name', 'stock__product_full_name')

        if profit_date_0 and profit_date_1:
            queryset = queryset.filter(
                (Q(sales__isnull=False) & Q(sales__is_purchase_return=False))
                | Q(purchase__is_sales_return=True),
            )
            # discard 0 purchase price containing stocks based on settings
            if ignore_zero_purchase == 'true':
                queryset = queryset.filter(
                    Q(stock__avg_purchase_rate__gt=0) |
                    Q(stock__product__purchase_price__gt=0)
                )
                # price_type = self.request.user.organization.organizationsetting.price_type
                # if price_type == PriceType.PRODUCT_PRICE:
                #     queryset = queryset.filter(stock__product__purchase_price__gt=0)
                # if price_type == PriceType.LATEST_PRICE:
                #     queryset = queryset.filter(stock__purchase_rate__gt=0)
                # else:
                #     queryset = queryset.filter(
                #         Q(stock__product__purchase_price__gt=0)|
                #         Q(stock__purchase_rate__gt=0))

            sales_filter = {
                'sales__isnull': False,
                'sales__is_purchase_return': False,
            }
            return_filter = {'purchase__is_sales_return': True}

            if profit_report_summary:
                queryset = queryset.values(
                    'stock__store_point__name',
                ).annotate(
                    total_quantity=Coalesce(Sum(Case(When(**sales_filter, then=('quantity')))), 0.00),
                    return_total_quantity=Coalesce(
                        Sum(Case(When(**return_filter, then=('quantity')))), 0.00),
                    received=Coalesce(Sum(Case(
                        When(secondary_unit_flag=True, **sales_filter, then=(
                            F('rate') / F('conversion_factor')
                        ) * F('quantity')),
                        When(secondary_unit_flag=False, **sales_filter, then=(
                            F('quantity') * F('rate'))),
                        output_field=FloatField(),
                    )), 0.00),
                    return_received=Coalesce(Sum(Case(
                        When(secondary_unit_flag=True, **return_filter, then=(
                            F('rate') / F('conversion_factor')
                        ) * F('quantity')),
                        When(secondary_unit_flag=False, **return_filter, then=(
                            F('quantity') * F('rate'))),
                        output_field=FloatField(),
                    )), 0.00),
                    discount=Coalesce(Sum(
                        Case(When(**sales_filter,
                            then=(F('discount_total') - F('round_discount'))))), 0.00),
                    return_discount=Coalesce(Sum(
                        Case(When(**return_filter,
                            then=(F('discount_total') - F('round_discount'))))), 0.00),
                    vat=Coalesce(Sum(Case(When(**sales_filter, then=('vat_total')))), 0.00),
                    return_vat=Coalesce(Sum(Case(When(**return_filter, then=('vat_total')))), 0.00),
                    return_calculated_price=Sum(
                        Case(
                            When(
                                calculated_price__gt=0, **return_filter,  then=(
                                    F('quantity') * F('calculated_price')
                                )
                            ),
                            When(
                                stock__product__purchase_price__gt=0, **return_filter, then=(
                                    F('quantity') * F('stock__product__purchase_price')
                                )
                            )
                        )
                    ) / F('return_total_quantity'),
                    calculated_price=Coalesce(Sum(
                        Case(
                            When(
                                calculated_price__gt=0, **sales_filter, then=(
                                    F('quantity') * F('calculated_price')
                                )
                            ),
                            When(
                                stock__product__purchase_price__gt=0, **sales_filter, then=(
                                    F('quantity') * F('stock__product__purchase_price')
                                )
                            )
                        )
                    ) / F('total_quantity'), 0.00),
                    avg_purchase_rate=Coalesce(Sum(
                        Case(
                            When(
                                stock__avg_purchase_rate__gt=0, **sales_filter,then=(
                                    F('quantity') * F('stock__avg_purchase_rate')
                                )
                            ),
                            When(
                                stock__product__purchase_price__gt=0, **sales_filter, then=(
                                    F('quantity') * F('stock__product__purchase_price')
                                )
                            )
                        )
                    ) / F('total_quantity'), 0.00),
                ).annotate(
                    net_price=F('received') - F('discount') + F('vat'),
                    return_net_price=F('return_received') - F('return_discount') + F('return_vat'),
                    sales_profit=Coalesce(ExpressionWrapper(((NullIf(F('net_price'), 0.00) / NullIf(F('total_quantity'), 0)) -
                        F('avg_purchase_rate')) * F('total_quantity'), output_field=FloatField()), 0.00),
                    total_profit=ExpressionWrapper(F('sales_profit') - ((NullIf(F('return_net_price'), 0.00) /
                        F('return_total_quantity')) - F('return_calculated_price')) *
                        F('return_total_quantity'),
                        output_field=FloatField()),
                ).order_by('stock__store_point__name')

            else:
                queryset = queryset.values(
                    'stock__store_point__name',
                    'stock__product__name',
                    'stock__product__alias',
                    'stock__product__strength',
                    'stock__product__form__name',
                    'stock__product__manufacturing_company__name',
                    'stock__product__subgroup__product_group__type',
                    'stock__product__purchase_price',
                    'stock__stock',
                    'stock__id',
                    'stock__purchase_rate',
                ).annotate(
                    total_quantity=Coalesce(Sum(Case(When(**sales_filter, then=('quantity')))), 0.00),
                    return_total_quantity=Coalesce(
                        Sum(Case(When(**return_filter, then=('quantity')))), 0.00),
                    received=Coalesce(Sum(Case(
                        When(secondary_unit_flag=True, **sales_filter, then=(
                            F('rate') / F('conversion_factor')
                        ) * F('quantity')),
                        When(secondary_unit_flag=False, **sales_filter, then=(
                            F('quantity') * F('rate'))),
                        output_field=FloatField(),
                    )), 0.00),
                    return_received=Coalesce(Sum(Case(
                        When(secondary_unit_flag=True, **return_filter, then=(
                            F('rate') / F('conversion_factor')
                        ) * F('quantity')),
                        When(secondary_unit_flag=False, **return_filter, then=(
                            F('quantity') * F('rate'))),
                        output_field=FloatField(),
                    )), 0.00),
                    discount=Coalesce(Sum(
                        Case(When(**sales_filter,
                            then=(F('discount_total') - F('round_discount'))))), 0.00),
                    return_discount=Coalesce(Sum(
                        Case(When(**return_filter,
                            then=(F('discount_total') - F('round_discount'))))), 0.00),
                    vat=Coalesce(Sum(Case(When(**sales_filter, then=('vat_total')))), 0.00),
                    return_vat=Coalesce(Sum(Case(When(**return_filter, then=('vat_total')))), 0.00),
                    return_calculated_price=Coalesce(Sum(
                        Case(
                            When(
                                calculated_price__gt=0, **return_filter,  then=(
                                    F('quantity') * F('calculated_price')
                                )
                            ),
                            When(
                                stock__product__purchase_price__gt=0, **return_filter, then=(
                                    F('quantity') * F('stock__product__purchase_price')
                                )
                            )
                        )
                    ) / F('return_total_quantity'), 0.00),
                    calculated_price=Coalesce(ExpressionWrapper(Sum(
                        Case(
                            When(
                                calculated_price__gt=0, **sales_filter,  then=(
                                    F('quantity') * F('calculated_price')
                                )
                            ),
                            When(
                                stock__product__purchase_price__gt=0, **sales_filter, then=(
                                    F('quantity') * F('stock__product__purchase_price')
                                )
                            )
                        )
                    ) / NullIf(F('total_quantity'), 0.00),
                    output_field=FloatField()), 0.00),
                    avg_purchase_rate=F('stock__avg_purchase_rate'),
                    calculated_price_organization_wise=F(
                        'stock__calculated_price_organization_wise'),
                    net_price=F('received') - F('discount') + F('vat'),
                    return_net_price=F('return_received') - F('return_discount') + F('return_vat'),
                    sales_profit=Coalesce(ExpressionWrapper((((F('net_price')) / NullIf(F('total_quantity'), 0.00)) -
                        F('avg_purchase_rate')) * F('total_quantity'),
                        output_field=FloatField()), 0.00),
                    total_profit=Coalesce(NullIf(ExpressionWrapper(NullIf(F('sales_profit'), 0.00) - ((NullIf(F('return_net_price'), 0.00) /
                        NullIf(F('return_total_quantity'), 0.00)) - NullIf(F('return_calculated_price'), 0.00)) *
                        NullIf(F('return_total_quantity'), 0.00),
                        output_field=FloatField()), 0.00), 0.00)
                ).order_by('stock__store_point__name', 'stock__product_full_name')
            return queryset

        else:
            date = self.request.query_params.get('date_0')
            batch = self.request.query_params.get('batch')
            stock_demand = self.request.query_params.get('stock_demand')
            if date:
                query = queryset.filter(sales__isnull=False,)
                sold_item = query.values_list('stock__product__alias', flat=True)
                queryset = queryset.exclude(
                    stock__product__alias__in=sold_item
                ).order_by(
                    'stock__store_point__name', 'stock__product_full_name', 'stock__id'
                ).distinct(
                    'stock__store_point__name', 'stock__product_full_name', 'stock__id'
                )

            elif batch:
                queryset = queryset.values(
                    'stock',
                    'batch',
                    'stock__id',
                    'stock__product',
                    'stock__store_point',
                    'stock__store_point__name',
                    'stock__product__name',
                    'stock__product__alias',
                    'stock__product__strength',
                    'stock__product__form__name',
                    'stock__product__generic__name',
                    'stock__product__manufacturing_company__name',
                    'stock__product__subgroup__name',
                    'stock__product__subgroup__product_group__type',
                    'stock__product__subgroup__product_group__name',
                    'stock__product__purchase_price',
                    'stock__product__trading_price',
                    'stock__stock',
                    'stock__purchase_rate',
                    'stock__sales_rate',
                    'stock__calculated_price',
                    'stock__minimum_stock',
                ).annotate(
                    last_usage=Max('date'),
                    expire_date=Min('expire_date'),
                    quantity=Coalesce(Sum(Case(When(
                        type=StockIOType.INPUT,
                        then=F('quantity')))), 0.00) -\
                        Coalesce(Sum(Case(When(
                            type=StockIOType.OUT,
                            then=F('quantity')))), 0.00),
                ).order_by(
                    'stock__store_point__name', 'stock__product_full_name',
                    'stock__product__manufacturing_company', 'batch'
                )
                return queryset

            elif stock_demand == 'true':
                queryset = self.get_product_under_demand_stock_report()
            else:
                queryset = queryset.filter(
                    type=StockIOType.INPUT
                ).order_by(
                    'stock__store_point__name', 'stock__product_full_name', 'stock__id'
                ).distinct(
                    'stock__store_point__name', 'stock__product_full_name', 'stock__id'
                )

            return queryset


class ProductLastUsageDate(ListAPIView):
    """
    takes: list of products and store point aliases
    return: product last usage time, product id, store point id
    """
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsNurse,
        StaffIsAdmin,
        StaffIsSalesman,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = ProductLastUsageDateSerializer
    pagination_class = None

    def get_queryset(self):
        batch = self.request.query_params.get('batch', None)
        stocks = self.request.query_params.get('stocks', None)

        if stocks:
            stock_list = stocks.split(',')
            stock_list = list(filter(not_blank(), stock_list))
            queryset = StockIOLog.objects.filter(
                organization=self.request.user.organization_id,
                status=Status.ACTIVE,
                stock__alias__in=stock_list,
            )
            if batch:
                batch_list = batch.split(',')
                batch_list = list(filter(not_blank(False), batch_list))
                queryset = queryset.filter(
                    batch__in=batch_list,
                )
                queryset = queryset.values(
                    'stock',
                    'batch'
                )
            else:
                queryset = queryset.values(
                    'stock',
                )
            queryset = queryset.annotate(
                last_usage=Max('date'),
            ).order_by('stock')

        else:
            queryset = StockIOLog.objects.none()
        return queryset


class StockDetailsReport(ListAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    # pagination_class = None
    permission_classes = (CheckAnyPermission, )
    serializer_class = StockDetailsReportSerializer

    def get_queryset(self):
        store_points = self.request.query_params.get('store_point', None)
        groups = self.request.query_params.get('product_group', None)
        companies = self.request.query_params.get('company', None)
        start_date = self.request.query_params.get('date_0', None)
        end_date = self.request.query_params.get('date_1', None)
        show_io_products = self.request.query_params.get('show_io_products', None)
        values = {
            'product__is_service': False,
            'product__status': Status.ACTIVE,
            'stocks_io__status': Status.ACTIVE,
            # 'stocks_io__date__range': [start_date, end_date]
        }
        if store_points:
            # prepare store points alias list after validating uuid
            store_point_list = list(filter(not_blank(), store_points.split(',')))
            if store_point_list:
                values['store_point__alias__in'] = store_point_list
        if groups:
            # prepare company alias list after validating uuid
            group_list = list(filter(not_blank(), groups.split(',')))
            if group_list:
                values['product__subgroup__product_group__alias__in'] = group_list
        if companies:
            # prepare company alias list after validating uuid
            company_list = list(filter(not_blank(), companies.split(',')))
            if company_list:
                values['product__manufacturing_company__alias__in'] = company_list
        arguments = {}
        for key, value in values.items():
            if value is not None:
                arguments[key] = value
        query = Stock().get_active_from_organization(
            self.request.user.organization_id
        ).filter(
            **arguments
        )
        if show_io_products and show_io_products == 'true':
            query = query.filter(
                stocks_io__isnull=False,
                stocks_io__date__range=[start_date, end_date]
            )
        query = query.values(
            'store_point__alias',
            'store_point__name',
            'product',
            'product__name',
            'product__full_name',
            'product__alias',
            'product__strength',
            'product__form__name',
            'product__generic__name',
            'product__manufacturing_company__name',
            'product__subgroup__name',
            'product__subgroup__product_group__type',
            'product__subgroup__product_group__name',
            'purchase_rate'
        ).annotate(
            sales_sum=Coalesce(Sum(Case(When(
                stocks_io__sales__isnull=False,
                stocks_io__date__range=[start_date, end_date],
                then=F('stocks_io__quantity')))), 0.00),
            sales_price=Coalesce(Sum(Case(When(
                stocks_io__sales__isnull=False,
                stocks_io__date__range=[start_date, end_date],
                then=F('stocks_io__sales__amount')))), 0.00) / Coalesce(Sum(Case(When(
                    stocks_io__sales__isnull=False,
                    stocks_io__date__range=[start_date, end_date],
                    then=F('stocks_io__quantity')))), 1),
            purchase_sum=Coalesce(Sum(Case(When(
                stocks_io__purchase__isnull=False,
                stocks_io__date__range=[start_date, end_date],
                then=F('stocks_io__quantity')))), 0.00),
            purchase_price=Coalesce(Sum(Case(When(
                stocks_io__purchase__isnull=False,
                stocks_io__date__range=[start_date, end_date],
                then=F('stocks_io__purchase__amount')))), 0.00) / Coalesce(Sum(Case(When(
                    stocks_io__purchase__isnull=False,
                    stocks_io__date__range=[start_date, end_date],
                    then=F('stocks_io__quantity')))), 1),
            transfer_in=Coalesce(Sum(Case(When(
                stocks_io__transfer__isnull=False,
                stocks_io__type=StockIOType.INPUT,
                stocks_io__date__range=[start_date, end_date],
                then=F('stocks_io__quantity')))), 0.00),
            transfer_out=Coalesce(Sum(Case(When(
                stocks_io__transfer__isnull=False,
                stocks_io__type=StockIOType.OUT,
                stocks_io__date__range=[start_date, end_date],
                then=F('stocks_io__quantity')))), 0.00),
            disbursement=Coalesce(Sum(Case(When(
                stocks_io__adjustment__is_product_disbrustment=True,
                stocks_io__date__range=[start_date, end_date],
                then=F('stocks_io__quantity')))), 0.00),
            adjustment_in=Coalesce(Sum(Case(When(
                stocks_io__adjustment__is_product_disbrustment=False,
                stocks_io__type=StockIOType.INPUT,
                stocks_io__date__range=[start_date, end_date],
                then=F('stocks_io__quantity')))), 0.00),
            adjustment_out=Coalesce(Sum(Case(When(
                stocks_io__adjustment__is_product_disbrustment=False,
                stocks_io__type=StockIOType.OUT,
                stocks_io__date__range=[start_date, end_date],
                then=F('stocks_io__quantity')))), 0.00),
            opening_stock=Coalesce(Sum(Case(When(
                stocks_io__type=StockIOType.INPUT,
                stocks_io__date__lt=start_date,
                then=F('stocks_io__quantity')))), 0.00) -\
                Coalesce(Sum(Case(When(
                    stocks_io__type=StockIOType.OUT,
                    stocks_io__date__lt=start_date,
                    then=F('stocks_io__quantity')))), 0.00),
        ).order_by('product_full_name')
        return query

    def list(self, request):
        serializer = StockDetailsReportSerializer(
            self.get_queryset(), many=True, context={'request': self.request})
        # for i in range(len(serializer.data)):
        #     for j in opening_stocks:
        #         if j['stock__product'] == serializer.data[i]['product']['id']:
        #             serializer.data[i]['opening_stock'] = j['sum']
        page = self.paginate_queryset(self.get_queryset())
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class InventorySummary(ListAPIView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    pagination_class = None
    permission_classes = (CheckAnyPermission, )
    serializer_class = InventorySummarySerializer

    def get_queryset(self):
        store_points = self.request.query_params.get('store_points', None)
        if store_points:
            store_points = store_points.split(',')
        product = self.request.query_params.get('product', None)
        start_date = self.request.query_params.get('date_0', None)
        end_date = self.request.query_params.get('date_1', None)
        inventory_type = self.request.query_params.get('inventory_type', None)
        values = {
            'stock__store_point__alias__in': store_points,
            'stock__product__alias': product,
            'stock__product__status': Status.ACTIVE,
            'stock__status': Status.ACTIVE,
            'date__range': [start_date, end_date]
        }
        if inventory_type:
            inventory_type = int(inventory_type)
            # fetch only stock adjustment related stockiolog
            if inventory_type in [InventoryType.ADJUSTMENT_IN, InventoryType.ADJUSTMENT_OUT]:
                values['adjustment__isnull'] = False
                values['adjustment__is_product_disbrustment'] = False
                # Adjustment IN
                if inventory_type == InventoryType.ADJUSTMENT_IN:
                    values['type'] = StockIOType.INPUT
                # Adjustment OUT
                else:
                    values['type'] = StockIOType.OUT
            # fetch only stock transfer related stockiolog
            if inventory_type in [InventoryType.TRANSFER_IN, InventoryType.TRANSFER_OUT]:
                values['transfer__isnull'] = False
                # Transfer IN
                if inventory_type == InventoryType.TRANSFER_IN:
                    values['type'] = StockIOType.INPUT
                # Transfer OUT
                else:
                    values['type'] = StockIOType.OUT
        arguments = {}
        for key, value in values.items():
            if value is not None:
                arguments[key] = value
        query = StockIOLog().get_active_from_organization(
            self.request.user.organization_id
        ).filter(
            **arguments
        )
        query = filter_data_by_user_permitted_store_points(self, query, 'stock__store_point')
        query = query.values(
            'date',
            'stock__store_point__name',
        ).annotate(
            quantity=Coalesce(Sum('quantity'), 0.00)
        ).order_by('date', 'stock__store_point__name')
        return query


class ProductStockSummaryReport(ListAPIView):
    """Report to fetch storepoint-wise stock summary
    for given date range of a selected product
    """
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    pagination_class = None
    permission_classes = (CheckAnyPermission, )

    def get_queryset(self):
        products = self.request.query_params.get('product', None)
        start_date = self.request.query_params.get('date_0', None)
        end_date = self.request.query_params.get('date_1', None)
        values = {
            'date__range': [start_date, end_date]
        }
        if products:
            # prepare product alias list after validating uuid
            product_list = list(filter(not_blank(), products.split(',')))
            if product_list:
                values['stock__product__alias__in'] = product_list
        if None in values['date__range']:
            values['date__range'] = None
        arguments = {}
        for key, value in values.items():
            if value is not None:
                arguments[key] = value
        return StockIOLog().get_active_from_organization(
            self.request.user.organization_id
        ).select_related('stock__store_point').filter(
            **arguments
        )

    def list(self, request):
        queryset = self.get_queryset().values(
            'stock__product',
            'stock__store_point',
            'stock__store_point__name',
            'stock__product__name',
            'stock__product__alias',
            'stock__product__form__name',
            'stock__product__generic__name',
            'stock__product__manufacturing_company__name',
            'stock__product__subgroup__name',
            'stock__product__subgroup__product_group__type',
            'stock__product__subgroup__product_group__name',
            'stock__product__purchase_price',
            'stock__stock',
            'stock__purchase_rate',
        ).annotate(
            sales_sum=Coalesce(Sum(Case(When(
                sales__isnull=False,
                then=F('quantity')))), 0.00),
            purchase_sum=Coalesce(Sum(Case(When(
                purchase__isnull=False,
                then=F('quantity')))), 0.00),
            transfer_in=Coalesce(Sum(Case(When(
                transfer__isnull=False,
                type=StockIOType.INPUT,
                then=F('quantity')))), 0.00),
            transfer_out=Coalesce(Sum(Case(When(
                transfer__isnull=False,
                type=StockIOType.OUT,
                then=F('quantity')))), 0.00),
            disbursement=Coalesce(Sum(Case(When(
                adjustment__is_product_disbrustment=True,
                then=F('quantity')))), 0.00),
            adjustment_in=Coalesce(Sum(Case(When(
                adjustment__is_product_disbrustment=False,
                type=StockIOType.INPUT,
                then=F('quantity')))), 0.00),
            adjustment_out=Coalesce(Sum(Case(When(
                adjustment__is_product_disbrustment=False,
                type=StockIOType.OUT,
                then=F('quantity')))), 0.00),
        ).order_by('stock__product', 'stock__store_point__name')
        serializer = ProductStockReportSerializer(queryset, many=True)
        return Response(serializer.data)


class StockAdjustmentList(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdjustment,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )
    filterset_class = StockAdjustmentFilter
    cache_name = 'stock_adjustment'

    def get_queryset(self):
        organization_id = str(format(self.request.user.organization_id, '04d'))
        key_stock_adjustment_list = '{}_list_{}'.format(self.cache_name, organization_id)
        cached_stock_adjustment_list = cache.get(key_stock_adjustment_list)

        if cached_stock_adjustment_list and False:
            data = cached_stock_adjustment_list
        else:
            data = StockAdjustment.objects.filter(
                organization=self.request.user.organization_id,
                is_product_disbrustment=False,
                status=Status.ACTIVE,
            ).exclude(adjustment_type=AdjustmentType.AUTO).select_related(
                'store_point',
                'person_organization_employee',
            ).only(
                'id',
                'alias',
                'date',
                'store_point',
                'store_point__alias',
                'store_point__name',
                # 'store_point__phone',
                # 'store_point__address',
                # 'store_point__type',
                'person_organization_employee',
                'person_organization_employee__alias',
                'person_organization_employee__first_name',
                'person_organization_employee__last_name',
                'person_organization_employee__phone',
                'person_organization_employee__person_group',
            ).order_by('-id')
            # cache.set(key_stock_adjustment_list, data)

        data = filter_data_by_user_permitted_store_points(self, data)
        return data

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StockAdjustmentModelSerializer.List
        else:
            return StockAdjustmentSerializer


    @transaction.atomic
    def create(self, request):
        try:
            with transaction.atomic():
                serializer = StockAdjustmentSerializer(
                    data=request.data, context={'request': request})
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    # organization_id = str(format(self.request.user.organization_id, '04d'))
                    # key_stock_adjustment_list = '{}_list_{}'.format(self.cache_name, organization_id)
                    # cache.delete_pattern(key_stock_adjustment_list)
                    return Response(serializer.data,
                                    status=status.HTTP_201_CREATED)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class StockAdjustmentDetails(RetrieveUpdateDestroyAPICustomView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
        StaffIsAdjustment,
    )
    permission_classes = (CheckAnyPermission, )

    lookup_field = 'alias'

    def get_queryset(self):
        disbursement_causes = StockIOLogDisbursementCause.objects.filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id
        )
        io_logs = StockIOLog.objects.prefetch_related(
            Prefetch(
                'io_log_disbursement_causes',
                queryset=disbursement_causes,
                to_attr='causes')
        ).filter(
            status=Status.ACTIVE,
            organization=self.request.user.organization_id
        ).select_related(
            'stock__store_point',
            'stock__product__manufacturing_company',
            'stock__product__form',
            'stock__product__subgroup__product_group',
            'stock__product__generic',
            'stock__product__primary_unit',
            'stock__product__secondary_unit',
            'stock__product__category',
        )
        return StockAdjustment.objects.filter(
            status=Status.ACTIVE
        ).prefetch_related(
            Prefetch('stock_io_logs', queryset=io_logs)
        ).select_related(
            'store_point',
            'person_organization_employee',
            'person_organization_patient',
            'employee__designation__department',
            'patient',
            'service_consumed'
        )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            adjustment = StockAdjustment.objects.get(
                alias=self.kwargs['alias'])
            if adjustment.is_product_disbrustment:
                return StockAdjustmentDetailsForDisburseSerializer
            return StockAdjustmentDetailsSerializer
        return StockAdjustmentBasicSerializer

    @transaction.atomic
    def perform_update(self, serializer):
        try:
            with transaction.atomic():
                if serializer.is_valid(raise_exception=True):
                    serializer.save(updated_by=self.request.user)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            raise APIException(content)

class StockDisbursementList(ListAPICustomView):
    available_permission_classes = (
        StaffIsProcurementOfficer,
        StaffIsAdmin,
    )
    permission_classes = (CheckAnyPermission, )
    filterset_class = StockDisbursementFilter
    serializer_class = StockDisbursementListSerializer

    def get_queryset(self):
        person_organization = self.request.query_params.get('person', None)
        queryset = StockAdjustment().get_active_from_organization(
            self.request.user.organization_id
        ).select_related(
            'store_point',
            'person_organization_patient',
            'person_organization_employee',
            'service_consumed',
            'service_consumed__subservice'
        ).filter(is_product_disbrustment=True).only(
            'id',
            'alias',
            'status',
            'date',
            'is_product_disbrustment',
            'store_point',
            'store_point__id',
            'store_point__alias',
            'store_point__name',
            'store_point__phone',
            'store_point__address',
            'store_point__type',
            'service_consumed',
            'service_consumed__id',
            'service_consumed__alias',
            'service_consumed__subservice',
            'service_consumed__subservice__id',
            'service_consumed__subservice__alias',
            'service_consumed__subservice__name',
            'person_organization_patient',
            'person_organization_patient__id',
            'person_organization_patient__alias',
            'person_organization_patient__code',
            'person_organization_patient__first_name',
            'person_organization_patient__last_name',
            'person_organization_patient__dob',
            'person_organization_patient__phone',
            'person_organization_patient__balance',
            'person_organization_patient__gender',
            # 'person_organization_patient__diagnosis_with',
            # 'person_organization_patient__economic_status',
            'person_organization_patient__person_group',
            'person_organization_employee__id',
            'person_organization_employee__alias',
            'person_organization_employee__first_name',
            'person_organization_employee__last_name',
            'person_organization_employee__phone',
            'person_organization_employee__person_group',
            'person_organization_employee__degree',
            'person_organization_employee__company_name',
        )
        queryset = filter_data_by_user_permitted_store_points(self, queryset)
        if person_organization:
            return queryset.filter(
                Q(person_organization_employee__alias=person_organization)
                | Q(person_organization_patient__alias=person_organization)
            ).order_by('-id')
        return queryset.order_by('-id')



class EmployeeStorePointAccessList(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsSalesman,
    )
    permission_classes = (CheckAnyPermission, )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EmployeeStorepointAccessSerializer
        else:
            return EmployeeStorepointAccessBasicSerializer

    def get_queryset(self):
        return EmployeeStorepointAccess().get_active_from_organization(
            self.request.user.organization_id)


class EmployeeStorePointDetails(RetrieveUpdateDestroyAPICustomView):
    permission_classes = (StaffIsAdmin,)
    lookup_field = 'alias'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EmployeeStorepointAccessSerializer
        else:
            return EmployeeStorepointAccessBasicSerializer

    def get_queryset(self):
        return EmployeeStorepointAccess().get_active_from_organization(
            self.request.user.organization_id)


class EmployeeStorePointList(ListAPIView):
    """Store Point List Accessed by an Employee"""
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsSalesman,
    )
    permission_classes = (CheckAnyPermission, )

    serializer_class = EmployeeStorepointAccessSerializer
    lookup_field = 'employee-alias'
    pagination_class = None

    def get_queryset(self):
        employee_alias = self.kwargs['employee_alias']
        query = EmployeeStorepointAccess.objects.filter(
            organization=self.request.user.organization_id,
            employee__alias=employee_alias,
            access_status=True,
            status=Status.ACTIVE,
        ).select_related(
            'store_point',
        ).order_by('pk')
        return query


class EmployeeAllStorePointList(ListAPIView):
    permission_classes = (StaffIsAdmin,)
    serializer_class = EmployeeStorepointAccessSerializer
    lookup_field = 'employee-alias'
    pagination_class = None

    def get_queryset(self):
        employee_alias = self.kwargs['employee_alias']
        query = EmployeeStorepointAccess.objects.filter(
            organization=self.request.user.organization_id,
            employee__alias=employee_alias,
            status=Status.ACTIVE,
        ).select_related(
            'store_point',
        ).exclude(store_point__type=StorePointType.VENDOR_DEFAULT).order_by('pk')
        return query


class EmployeeAccountList(ListAPIView):
    """Account List Accessed by an Employee"""
    permission_classes = (StaffIsAdmin,)
    serializer_class = EmployeeAccountAccessSerializer
    lookup_field = 'employee-alias'
    pagination_class = None

    def get_queryset(self):
        employee_alias = self.kwargs['employee_alias']
        query = EmployeeAccountAccess.objects.filter(
            organization=self.request.user.organization_id,
            employee__alias=employee_alias,
            access_status=True,
            status=Status.ACTIVE,
        ).select_related(
            'account',
        ).order_by('pk')
        return query


class EmployeeAllAccountList(ListAPIView):
    permission_classes = (StaffIsAdmin,)
    serializer_class = EmployeeAccountAccessSerializer
    lookup_field = 'employee-alias'
    pagination_class = None

    def get_queryset(self):
        employee_alias = self.kwargs['employee_alias']
        query = EmployeeAccountAccess.objects.filter(
            organization=self.request.user.organization_id,
            employee__alias=employee_alias,
            status=Status.ACTIVE,
        ).select_related(
            'account',
        ).order_by('pk')
        return query


class EmployeeAccountDetails(RetrieveUpdateDestroyAPICustomView):
    permission_classes = (StaffIsAdmin,)
    lookup_field = 'alias'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EmployeeAccountAccessSerializer
        else:
            return EmployeeAccountAccessBasicSerializer

    def get_queryset(self):
        return EmployeeAccountAccess().get_active_from_organization(
            self.request.user.organization_id)


class UnitList(ListCreateAPICustomView):
    serializer_class = UnitSerializer
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission, )
    cache_name = 'list'
    cached_model_name = 'unit'
    deleted_cache_model_list = [cached_model_name]

    def get_queryset(self):
        queryset = super(UnitList, self).get_queryset()
        skiped_units = get_global_based_discarded_list(self)
        queryset = queryset.exclude(pk__in=skiped_units)
        queryset = sync_queryset(self, queryset)
        return queryset


class UnitDetails(RetrieveUpdateDestroyAPICustomView):
    serializer_class = UnitSerializer
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
        StaffIsProcurementManager,
        StaffIsProcurementCoordinator,
    )
    permission_classes = (CheckAnyPermission, )
    lookup_field = 'alias'
    deleted_cache_model_list = ['unit']


class UnitMerge(APIView):
    """ Merge two different units and inactive / clone
        the unwanted unit also replace unit in StockIoLog"""
    permission_classes = (StaffIsAdmin, )

    def check_global(self, unit, clone_unit):
        """
        Check unit is global or private
        """
        return {
            'base': unit.is_global != PublishStatus.PRIVATE,
            'clone': clone_unit.is_global != PublishStatus.PRIVATE
        }

    def update_existing_unit(self, keep_unit, clone_unit):
        """ update Existing Product Unit which is inactive"""

        products = Product.objects.filter(
            (Q(primary_unit=clone_unit) |
             Q(secondary_unit=clone_unit))
        )
        stock_io_logs = StockIOLog.objects.filter(
            (Q(primary_unit=clone_unit) |
             Q(secondary_unit=clone_unit))
        )

        # update clone unit containing Products
        for product in products:
            if product.primary_unit == clone_unit:
                product.primary_unit = keep_unit
            if product.secondary_unit == clone_unit:
                product.secondary_unit = keep_unit
            product.save(update_fields=['primary_unit', 'secondary_unit'])

        # update clone unit containing StockIoLogs
        for item in stock_io_logs:
            if item.primary_unit == clone_unit:
                item.primary_unit = keep_unit
            if item.secondary_unit == clone_unit:
                item.secondary_unit = keep_unit
            item.save(update_fields=['primary_unit', 'secondary_unit'])

    def post(self, request):
        try:
            serializer = UnitMergeSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                # That unit want to keep
                unit = Unit.objects.get(id=serializer.data['unit'])
                # That unit will be inactive
                clone_unit = Unit.objects.get(id=serializer.data['clone_unit'])
                #check user is admin or superadmin
                _is_global = self.check_global(unit, clone_unit)

                # only super admin can merge two global unit
                if _is_global['base'] and _is_global['clone']:
                    if self.request.user.is_superuser:
                        self.update_existing_unit(unit, clone_unit)
                        clone_unit.status = Status.INACTIVE
                        clone_unit.save(update_fields=['status'])
                    else:
                        message = {
                            'error': '{}'.format("YOU_CAN_NOT_MERGE_TWO_GLOBAL_UNIT")
                        }
                        return Response(message, status=status.HTTP_400_BAD_REQUEST)
                # if a global unit is attempted to merged by
                # private unit then not to Inactive
                # this global unit just put it as private's clone
                elif not _is_global['base'] and _is_global['clone']:
                    self.update_existing_unit(unit, clone_unit)
                    unit.clone = clone_unit
                    unit.save(update_fields=['clone'])
                # if two unit are private or
                # private merged by global unit
                else:
                    self.update_existing_unit(unit, clone_unit)
                    clone_unit.status = Status.INACTIVE
                    clone_unit.save(update_fields=['status'])

                return Response(serializer.data, status=status.HTTP_200_OK)
        except IndentationError as exception:
            context = {'error': '{}'.format(exception)}
            return Response(context, status=status.HTTP_400_BAD_REQUEST)


class ProductMerge(APIView):
    """
    Merge two different products.
    Inactive a product and replace all stock of this product
    """
    permission_classes = (StaffIsAdmin, )

    @transaction.atomic
    def post(self, request):
        try:
            with transaction.atomic():
                serializer = ProductMergeSerializer(data=request.data)
                if serializer.is_valid(raise_exception=True):

                    primary_product = serializer.data['product']
                    mergeable_product = serializer.data['clone_product']

                    # merge mergeable_product with primary_product
                    merged = merge_two_products(
                        self.request.user.organization_id,
                        primary_product,
                        mergeable_product
                    )
                    if not merged:
                        error = {
                            "error": "NO_RELATED_STOCK_FOUND_FOR_PRIMARY_PRODUCT"
                        }
                        return Response(error, status=status.HTTP_400_BAD_REQUEST)

                    return Response(serializer.data, status=status.HTTP_200_OK)

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class ProductDisbursementCauseList(ListCreateAPICustomView):
    serializer_class = ProductDisbursementCauseModelSerializer.List
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer
    )
    permission_classes = (CheckAnyPermission, )
    cache_name = 'list'
    cached_model_name = 'product_disbursement_cause'
    deleted_cache_model_list = [cached_model_name]


class ProductDisbursementCauseDetails(RetrieveUpdateDestroyAPICustomView):
    serializer_class = ProductDisbursementCauseModelSerializer.List
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer
    )
    permission_classes = (CheckAnyPermission, )
    lookup_field = 'alias'
    deleted_cache_model_list = ['product_disbursement_cause']


class ProductShortList(ListAPIView):
    # serializer_class = ProductShortReportSerializer.List
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsSalesman,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission, )

    def get_serializer_class(self):
        if self.request.query_params.get('show_details', False) == 'true':
            return ProductShortReportSerializer.Details
        return ProductShortReportSerializer.List

    def get_queryset(self):
        start_date = self.request.query_params.get('date_0', str(datetime.date.today() + relativedelta(days=-7)))
        end_date = self.request.query_params.get('date_1', str(datetime.date.today()))
        start_date = get_datetime_obj_from_datetime_str(
            start_date,
            '%Y-%m-%d %H:%M:%S',
            "00:00:00"
        )
        end_date = get_datetime_obj_from_datetime_str(
            end_date,
            '%Y-%m-%d %H:%M:%S',
            "23:59:59",
        )
        sales_qty_filters = {
            "stocks_io__sales__isnull": False,
            "stocks_io__sales__is_purchase_return": False,
            "stocks_io__status": Status.ACTIVE,
            "stocks_io__sales__status": Status.ACTIVE,
            "stocks_io__sales__sale_date__range": [start_date, end_date],
        }
        values = {
            'store_point__alias': self.request.query_params.get('store_point', None),
            'organization': self.request.user.organization_id,
            'status': Status.ACTIVE,
        }
        arguments = {}
        for key, value in values.items():
            if value is not None and str(value) != '':
                arguments[key] = value
        queryset = Stock.objects.filter(
            stock__lte=F('minimum_stock'),
            **arguments
        ).select_related(
            'product',
            'store_point',
            'latest_purchase_unit',
        ).annotate(
            sale_qty=Coalesce(Sum(Case(When(
                **sales_qty_filters,
                then=F('stocks_io__quantity')))), 0.0),
        ).exclude(
            minimum_stock=0
        ).order_by('product__name')

        # product filter
        product = self.request.query_params.get('product', None)
        if product and product != "":
            products = product.split(",")
            queryset = queryset.filter(
                product__alias__in=products
            )

        # company filter
        company = self.request.query_params.get('company', None)
        if company and company != "":
            company_list = company.split(",")
            queryset = queryset.filter(
                product__manufacturing_company__alias__in=company_list
            )

        supplier = self.request.query_params.get('person', None)
        if supplier:
            queryset = queryset.filter(
                stocks_io__purchase__person_organization_supplier__alias=supplier
            ).order_by('product').distinct()

        # supplier filter
        # supplier = self.request.query_params.get('person', None)
        # if supplier:
        #     stock_io_logs = StockIOLog.objects.filter(
        #         status=Status.ACTIVE,
        #         organization=self.request.user.organization,
        #         date__gte=self.request.query_params.get('date_0'),
        #         date__lte=self.request.query_params.get('date_1'),
        #         purchase__person_organization_supplier__alias=supplier,
        #     )
        #     io_logs_stock = list(stock_io_logs.values_list(
        #         'stock__pk', flat=True))
        #     queryset = queryset.prefetch_related(
        #         Prefetch('stocks_io', queryset=stock_io_logs)
        #     ).filter(pk__in=io_logs_stock)
        return queryset


class StoreWiseSalesGraphData(APIView):
    available_permission_classes = (
        StaffIsReceptionist,
        StaffIsAccountant,
        StaffIsAdmin,
        StaffIsLaboratoryInCharge,
        StaffIsProcurementOfficer,
        StaffIsSalesman,
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        date_range = helpers.prepare_date_filter_with_period_value(request)
        queryset = Sales.objects.filter(
            Q(sale_date__gte=date_range['start']),
            Q(sale_date__lte=date_range['end']),
            organization=self.request.user.organization_id,
            status=Status.ACTIVE,
            is_purchase_return=False
        ).extra(
            select={
                'sale_date': "date(sale_date AT TIME ZONE '{0}')".format(
                timezone.get_current_timezone())
            }
        ).values('store_point__name', 'sale_date').annotate(
            value=Count('id')
        ).order_by('sale_date')

        serializer = StoreWiseSalesGraphSerializer(queryset, many=True)
        return Response({
            'data': prepare_for_sales_graph(serializer.data),
            'start_date': date_range['start'],
            'end_date': date_range['end'],
        })


class StoreWiseSalesAmountGraphData(APIView):
    available_permission_classes = (
        StaffIsReceptionist,
        StaffIsAccountant,
        StaffIsAdmin,
        StaffIsLaboratoryInCharge,
        StaffIsProcurementOfficer,
        StaffIsSalesman,
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        date_range = helpers.prepare_date_filter_with_period_value(request)
        queryset = Sales.objects.filter(
            Q(sale_date__gte=date_range['start']),
            Q(sale_date__lte=date_range['end']),
            organization=self.request.user.organization_id,
            status=Status.ACTIVE,
            is_purchase_return=False
        ).extra(
            select={
                'sale_date': "date(sale_date AT TIME ZONE '{0}')".format(
                timezone.get_current_timezone())
            }
        ).values('store_point__name', 'sale_date').annotate(
            value=Coalesce(Sum(F('amount')), 0.00) -
            Coalesce(Sum(F('discount')), 0.00) +
            Coalesce(Sum(F('vat_total')), 0.00) +
            Coalesce(Sum(F('round_discount')), 0.00),
        ).order_by('sale_date')

        serializer = StoreWiseSalesGraphSerializer(queryset, many=True)
        return Response({
            'data': prepare_for_sales_graph(serializer.data),
            'start_date': date_range['start'],
            'end_date': date_range['end'],
        })


class CompanyWiseSalesGraphData(APIView):
    available_permission_classes = (
        StaffIsReceptionist,
        StaffIsAccountant,
        StaffIsAdmin,
        StaffIsLaboratoryInCharge,
        StaffIsProcurementOfficer,
        StaffIsSalesman,
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        date_range = helpers.prepare_date_filter_with_period_value(request)
        queryset = Sales.objects.filter(
            Q(sale_date__gte=date_range['start']),
            Q(sale_date__lte=date_range['end']),
            organization=self.request.user.organization_id,
            status=Status.ACTIVE,
            is_purchase_return=False
        ).values(
            'stock_io_logs__stock__product__manufacturing_company__name'
        ).annotate(value=Count('id')).order_by('-value')

        total = 0
        for item in queryset:
            total += item['value']

        counted_queryset = queryset[:10]
        counted = 0
        for item in counted_queryset:
            counted += item['value']
        serializer = CompanyWiseSalesGraphSerializer(
            counted_queryset, many=True)
        data_list = serializer.data
        if total > counted:
            data_list = serializer.data + [{
                'name': 'Others',
                'y': total - counted
            }]

        return Response({
            'data': data_list,
            'start_date': date_range['start'],
            'end_date': date_range['end'],
        })


class GetHourlySalesAttributeList(ListAPIView):
    """ Hourly sales Report for a pharmacy.
    : total_sale: call a method with date and
    amount then return Salestime and total_amount as a list """

    available_permission_classes = (
        StaffIsReceptionist,
        StaffIsAccountant,
        StaffIsAdmin,
        StaffIsLaboratoryInCharge,
        StaffIsProcurementOfficer,
        StaffIsSalesman,
        StaffIsMonitor,
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, request):
        date = request.query_params.get('date', None)
        organization = request.user.organization
        organization_alias = request.query_params.get('organization', None)
        if organization_alias:
            organization_alias = organization_alias.split(',')
        total_sale = Sales().get_specific_attribute(
            'amount',
            date=date,
            object_filter={},
            primary_params='sale_date',
        ).filter(
            status=Status.ACTIVE,
            is_purchase_return=False,
        )
        if request.user.is_superuser or request.user.person_group == PersonGroupType.MONITOR:
            if organization_alias:
                total_sale = total_sale.filter(
                    organization__alias__in=organization_alias
                )
        else:
            total_sale = total_sale.filter(
                organization=organization
            )
        total_sale = total_sale.annotate(
            hour=ExtractHour('sale_date', fields.CharField()),
            minute=ExtractMinute('sale_date', fields.CharField()),
            time=Concat("hour", Value("."), "minute", output_field=fields.FloatField()),
            total_amount=Round(Coalesce(F('amount'), 0.00) - Coalesce(F('discount'), 0.00) +\
                Coalesce(F('transport'), 0.00) + Coalesce(F('vat_total'), 0.00) +\
                Coalesce(F('round_discount'), 0.00))
        ).values_list(
            "time", "total_amount"
        )
        return Response(total_sale)

class SalesVatReport(ListAPIView):
    """Report to show sales Vat, Vat rate
    for given date range of a selected StorePoint
    """
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission,)
    pagination_class = None

    def get(self, request):
        start_date = self.request.query_params.get('date_0', None)
        end_date = self.request.query_params.get('date_1', None)
        store_points = self.request.query_params.get('store_points', None)
        if store_points:
            store_points = store_points.split(',')
        values = {
            'organization': self.request.user.organization_id,
            'status': Status.ACTIVE,
            'vat_total__gt': 0,
            'date__range': [start_date, end_date],
            'sales__isnull': False,
            'sales__status': Status.ACTIVE,
            'sales__store_point__alias__in': store_points,
        }
        arguments = {}
        for key, value in values.items():
            if value is not None:
                arguments[key] = value

        queryset = StockIOLog.objects.filter(
            **arguments
        ).values(
            'date',
            'sales__store_point__name',
        ).annotate(
            base_sales=Case(
                When(
                    secondary_unit_flag=True,
                    then=Coalesce(
                        Sum((F('rate') / F('conversion_factor')) * F('quantity')), 0.00),
                    ),
                default=Coalesce(
                    Sum(F('rate') * F('quantity')), 0.00),
            ),
            total_sales=Case(
                When(
                    secondary_unit_flag=True,
                    then=Coalesce(
                        Sum(((F('rate') / F('conversion_factor')) * F('quantity')) +\
                            F('vat_total') - F('discount_total') + F('round_discount')), 0.00),
                    ),
                default=Coalesce(
                    Sum((F('rate') * F('quantity')) +\
                        F('vat_total') - F('discount_total') + F('round_discount')), 0.00),
            ),
            total_vat=Coalesce(Sum('vat_total'), 0.00),
            vat_rate=(F('total_vat') * 100) / F('base_sales')
        ).order_by('date', 'sales__store_point__name')
        return Response(queryset)


class PurchaseSummaryReport(ListAPIView):
    """
        Report to show purchase summary
        for given date range, store point and supplier
    """
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    serializer_class = PurchaseSummarySerializer
    filterset_class = PurchaseSummaryFilter
    permission_classes = (CheckAnyPermission,)

    def get_queryset(self):
        queryset = Purchase.objects.filter(
            organization=self.request.user.organization_id,
            status=Status.ACTIVE,
            is_sales_return=False,
            purchase_type=PurchaseType.PURCHASE,
        ).select_related(
            'store_point',
            'person_organization_supplier',
        )
        queryset = filter_data_by_user_permitted_store_points(self, queryset)
        queryset = queryset.values('store_point__name', 'person_organization_supplier__company_name').annotate(
            store=F('store_point__name'),
            purchase_date=Cast("purchase_date", fields.DateField()),
            supplier=F('person_organization_supplier__company_name'),
            purchase_count=Count('id'),
            total_purchase=Coalesce(Sum('amount'), 0.00),
            total_discount=Coalesce(Sum('discount'), 0.00) - Coalesce(Sum('round_discount'), 0.00),
            total_vat=Coalesce(Sum('vat_total'), 0.00),
            grand_total=Coalesce(Sum('grand_total'), 0.00),
        ).order_by('-purchase_date')
        return queryset


class ProductPurchaseSummary(ListAPIView):
    """
        Report to show product wise purchase summary
        for given date range, store point and supplier
    """
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    serializer_class = StockIoLogReportSerializer
    permission_classes = (CheckAnyPermission,)

    def get_queryset(self):
        date_0 = self.request.query_params.get('date_0', None)
        date_1 = self.request.query_params.get('date_1', None)
        person = self.request.query_params.get('person', None)
        store_point = self.request.query_params.get('store_point', None)

        filter_args = {}

        if date_0 and date_1:
            filter_args['date__range'] = [date_0, date_1]

        if person:
            filter_args['purchase__person_organization_supplier__alias__in'] = \
            list(filter(not_blank(), person.split(',')))

        if store_point:
            filter_args['purchase__store_point__alias__in'] = \
                list(filter(not_blank(), store_point.split(',')))

        queryset = StockIOLog.objects.filter(
            organization=self.request.user.organization_id,
            status=Status.ACTIVE,
            purchase__purchase_type=PurchaseType.PURCHASE,
            purchase__is_sales_return=False,
            **filter_args
        ).order_by('-date').values(
            'date',
            'purchase__store_point',
            'purchase__store_point__name',
            'purchase__person_organization_supplier',
            'purchase__person_organization_supplier__company_name',
            'stock__product',
            'stock__product__name',
            'stock__product__alias',
            'stock__product__strength',
            'stock__product__form__name',
            'stock__product__generic__name',
            'stock__product__manufacturing_company__name',
            'stock__product__subgroup__name',
            'stock__product__subgroup__product_group__type',
            'stock__product__subgroup__product_group__name',
        ).annotate(
            qty=Coalesce(Sum('quantity'), 0.00),
            amount=Coalesce(
                Sum(Case(
                    When(
                        secondary_unit_flag=True,
                        then=((F('quantity') / F('conversion_factor')) * F('rate'))
                    ),
                    default=(F('rate') * F('quantity')),
                    output_field=FloatField()
                )), 0
            ),
            vat=Coalesce(Sum('vat_total'), 0.00),
            discount=Coalesce(Sum('discount_total') - Sum('round_discount'), 0.00),
        )
        return queryset


class StoreWiseStockValue(APIView):
    available_permission_classes = (
        StaffIsAdmin
    )
    permission_classes = (CheckAnyPermission,)

    def get(self, _):
        store_point = self.request.query_params.get('store_point', None)
        stock = Stock.objects.filter(
            organization=self.request.user.organization_id,
            status=Status.ACTIVE,
            product__is_service=False,
            stocks_io__organization=self.request.user.organization_id,
            stocks_io__status=Status.ACTIVE
        ).only(
            'id',
            'product__purchase_price',
            'calculated_price'
        ).distinct()
        if store_point:
            stock = stock.filter(
                store_point__alias=store_point,
            )
        stock = stock.aggregate(
            stock_value=Coalesce(Sum(F('stock')* Case(
                When(
                    organization__organizationsetting__purchase_price_type=PriceType.PRODUCT_PRICE,
                    then=F('product__purchase_price')
                ),
                When(
                    organization__organizationsetting__purchase_price_type=PriceType.LATEST_PRICE_AND_PRODUCT_PRICE,
                    calculated_price__lte=0,
                    then=F('product__purchase_price')
                ),
                When(
                    organization__organizationsetting__purchase_price_type=PriceType.PRODUCT_PRICE_AND_LATEST_PRICE,
                    product__purchase_price__gt=0,
                    then=F('product__purchase_price')
                ),
                default=F('calculated_price'),
            )), 0.00),
        )
        return Response(stock)


class StockBulkUpdate(APIView):
    """
    Updating discount margin, rack and demand, if similar product
    belong to same company or same store points or product forms
    or product sub group or product
    """
    available_permission_classes = (
        StaffIsAdmin
    )
    permission_classes = (CheckAnyPermission,)
    chunk_size = 5000

    def chunk_update_stock(self, stocks):
        """
        stocks: queryset object
        """
        update_data = {}
        for key in self.request.data.keys():
            update_data[key] = self.request.data[key]
        dict_ = stocks.aggregate(Max('id'), Min('id'))
        max_id = dict_['id__max']
        min_id = dict_['id__min']
        while min_id <= max_id:
            max_range = min_id + self.chunk_size - 1
            max_range = max_id if max_range > max_id else max_range
            stocks.filter(
                pk__range=[min_id, max_range],
            ).update(**update_data)
            min_id += self.chunk_size

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                filter_arguments = stock_specific_attribute_filter(self.request.GET)
                stocks = Stock.objects.filter(
                    status=Status.ACTIVE,
                    organization=self.request.user.organization_id,
                    **filter_arguments,
                )
                if stocks.exists():
                    # update chunk stock
                    self.chunk_update_stock(stocks)

                    stocks = stocks.values_list('id', flat=True)
                    # create chunk of size 5000 then expire cache of these stock
                    base_key = 'stock_instance'
                    for item in range(0, stocks.count(), self.chunk_size):
                        chunk = stocks[item : item + self.chunk_size]
                        # expire cache
                        cache_key_list = ["{}_{}".format(base_key, str(stock_id).zfill(12)) \
                            for stock_id in chunk]
                        cache_expire_list.apply_async(
                            (cache_key_list, ),
                            countdown=5,
                            retry=True, retry_policy={
                                'max_retries': 10,
                                'interval_start': 0,
                                'interval_step': 0.2,
                                'interval_max': 0.2,
                            }
                        )
                return Response(
                    {'count': stocks.count()},
                    status=status.HTTP_200_OK
                )

        except IntegrityError as exception:
            content = {'error': '{}'.format(exception)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class DistributorOrderLimitPerDay(APIView):
    """Get order limit per day for product of a distributor"""
    available_permission_classes = (
        StaffIsAdmin,
        StaffIsProcurementOfficer,
    )
    permission_classes = (CheckAnyPermission, )

    def get(self, request, stock_alias):
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        is_queueing_order = self.request.query_params.get('is_queueing_order', None)
        user_details = get_user_profile_details_from_cache(request.user.id)
        if checkers.is_uuid(stock_alias):
            stock_filter = { 'alias': stock_alias }
            stock_io_filter = { 'stock__alias': stock_alias }
        else:
            stock_filter = { 'id': stock_alias }
            stock_io_filter = { 'stock__id': stock_alias }
        stock = Stock.objects.only(
            'stock',
            'orderable_stock',
            'product',
            'organization'
        ).get(**stock_filter)
        distributor_settings = get_healthos_settings()
        product = Product.objects.values(
            'order_mode',
            'order_limit_per_day',
            'order_limit_per_day_mirpur',
            'order_limit_per_day_uttara',
            'is_queueing_item',
            'minimum_order_quantity',
        ).get(pk=stock.product_id)
        if distributor_settings.overwrite_order_mode_by_product:
            order_mode = product.get('order_mode')
        else:
            order_mode = distributor_settings.allow_order_from

        order_items = StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            organization=self.request.user.organization_id,
            date=current_date,
            **stock_io_filter
        ).exclude(
            purchase__current_order_status__in=[OrderTrackingStatus.REJECTED, OrderTrackingStatus.CANCELLED]
        ).values(
            'purchase__distributor_order_type'
        ).annotate(total_qty=Coalesce(Sum(F('quantity')), 0.00)).order_by()

        order_items_data = list(order_items)

        order_item = next(filter(lambda item: item['purchase__distributor_order_type'] == DistributorOrderType.ORDER, order_items_data), {})
        cart_item = next(filter(lambda item: item['purchase__distributor_order_type'] == DistributorOrderType.CART, order_items_data), {})

        try:
            # get order limit value based on delivery hub short_code
            short_code = user_details.organization.delivery_hub.short_code

            if short_code == "MH-1":
                order_limit = product.get("order_limit_per_day_mirpur")
            elif short_code == "UH-1":
                order_limit = product.get("order_limit_per_day_uttara")
            else:
                order_limit = product.get("order_limit_per_day")
        except AttributeError:
            order_limit = product.get("order_limit_per_day")

        limit_data = {
            "today": current_date,
            "order_quantity": order_item.get('total_qty', 0),
            "cart_quantity": cart_item.get('total_qty', 0),
            "order_limit": order_limit,
            "allow_order_from": order_mode,
            "is_out_of_stock": stock.is_out_of_stock,
            "orderable_stock": stock.orderable_stock,
            "minimum_order_quantity": product.get("minimum_order_quantity", 1)

        }
        # if order mode is from organization and its Stock and Open
        # we only allow the product with order mode stock or open
        original_order_mode = None
        if order_mode == AllowOrderFrom.STOCK_AND_OPEN:
            order_mode = product.get('order_mode')
            original_order_mode = AllowOrderFrom.STOCK_AND_OPEN

        if (
            (order_mode == AllowOrderFrom.OPEN) or
            (order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY and product.get('is_queueing_item'))
            ):
            limit_data['rest_quantity'] = limit_data['order_limit'] - (limit_data['order_quantity'] + limit_data['cart_quantity'])
        elif (
            (order_mode == AllowOrderFrom.STOCK) or
            (order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY and not product.get('is_queueing_item'))
            ):
            # limit_data['rest_quantity'] = min((limit_data['order_limit'] - (limit_data['order_quantity'] + limit_data['cart_quantity'])), (limit_data.get('orderable_stock') - (limit_data['order_quantity'] + limit_data['cart_quantity'])))
            limit_data['rest_quantity'] = min((limit_data['order_limit'] - (limit_data['order_quantity'] + limit_data['cart_quantity'])), (limit_data.get('orderable_stock') - (limit_data['cart_quantity'])))
        elif (
            (original_order_mode == AllowOrderFrom.STOCK_AND_OPEN) and
            order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY and
            limit_data.get("orderable_stock", 0) >= 0
        ):
            limit_data['rest_quantity'] = 0

        limit_data['add_to_queue'] = (order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY and (limit_data.get("rest_quantity", 0) <= 0 or product.get('is_queueing_item')))

        if original_order_mode == AllowOrderFrom.STOCK_AND_OPEN:
            limit_data['add_to_queue'] = False
        return Response(limit_data, status=status.HTTP_200_OK)
