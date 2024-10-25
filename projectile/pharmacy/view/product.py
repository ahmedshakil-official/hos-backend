import datetime
import os
from validator_collection import checkers
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db.models import Prefetch, Case, When

from common.helpers import (
    get_enum_key_by_value,
    send_message_to_mattermost_by_channel_id,
)
from core.enums import AllowOrderFrom
from core.permissions import (
    CheckAnyPermission,
    StaffIsAdmin,
    IsSuperUser,
    StaffIsProcurementManager,
)
from core.views.common_view import ListAPICustomView, ListCreateAPICustomView
from search.utils import update_stock_es_doc
from pharmacy.custom_serializer.product import ProductModelSerializer
from pharmacy.custom_serializer.product_damage_recheck import (
    DamageProductListSerializer,
    DamageProductDetailSerializer,
    RecheckProductListSerializer,
    RecheckProductDetailSerializer,
    DamageItemsSerializer,
    RecheckProductsSerializer,
)
from pharmacy.models import Product, ProductChangesLogs, Stock, Damage, Recheck, DamageProduct, RecheckProduct
from pharmacy.filters import ProductFilter, DamageItemFilter


class ProductPropertiesBulkUpdate(APIView):
    """
    Update product properties(is_salesable, is_flash_item, is_published, order_mode) in bulk
    """

    def post(self, request):
        data = request.data
        channel_id = os.environ.get('PRODUCT_CHANGE_LOG_CHANNEL_ID')

        if not isinstance(data, list):
            return Response({"detail": _("PLEASE_SEND_DATA_AS_A_LIST")}, status=status.HTTP_400_BAD_REQUEST)

        aliases = [item["alias"] for item in data]

        obj_to_update = []
        products_before_update = []
        for item in data:
            item_keys = item.keys()
            product = Product.objects.filter(alias=item["alias"]).values(
                "id", "is_salesable", "is_published", "order_mode", "is_flash_item",
                "full_name", "stock_list__id", "trading_price", "discount_rate", "minimum_order_quantity"
            ).first()
            products_before_update.append(product)
            obj_to_update.append(
                Product(
                    id=product["id"],
                    is_salesable=item["is_salesable"] if "is_salesable" in item_keys else product["is_salesable"],
                    is_published=item["is_published"] if "is_published" in item_keys else product["is_published"],
                    order_mode=item["order_mode"] if "order_mode" in item_keys else product["order_mode"],
                    is_flash_item=item["is_flash_item"] if "is_flash_item" in item_keys else product["is_flash_item"],
                    trading_price=item["trading_price"] if "trading_price" in item_keys else product["trading_price"],
                    discount_rate=item["discount_rate"] if "discount_rate" in item_keys else product["discount_rate"],
                    minimum_order_quantity=item["minimum_order_quantity"] if "minimum_order_quantity" in item_keys else product["minimum_order_quantity"],
                )
            )
        Product.objects.bulk_update(
            obj_to_update,
            ["is_salesable", "is_published", "order_mode", "is_flash_item", "trading_price", "discount_rate", "minimum_order_quantity"],
            batch_size=1000,
        )
        products_after_update = Product.objects.filter(alias__in=aliases).values(
            "id", "is_salesable", "is_published", "order_mode", "is_flash_item",
            "full_name", "stock_list__id", "trading_price", "discount_rate", "minimum_order_quantity"
        )

        # Retrieve all active stocks from the database
        active_stocks = Stock().get_all_actives()

        for product_information in data:
            # Check if priority information is available for the product
            if "priority" in product_information:
                priority = product_information.get("priority")
                stock = Stock().get_all_actives().filter(
                    product__alias = product_information.get("alias")
                )
                stock.update(priority = priority)

            if "is_ad_enabled" in product_information:
                is_ad_enabled = product_information.get("is_ad_enabled")
                stock = Stock().get_all_actives().filter(
                    product__alias = product_information.get("alias")
                )
                stock.update(is_ad_enabled = is_ad_enabled)

        changes_to_be_created = []
        product_updated_related_stock_id_list = []
        product_before_update_dict = {p['id']: p for p in products_before_update}
        bd_time_now = str(datetime.datetime.now().strftime("%I:%M %p, %d %B, %Y"))
        message = f'**{request.user.get_full_name()}** has updated the following products at **{bd_time_now}**.'
        for product in products_after_update:
            product_updated_related_stock_id_list.append(product['stock_list__id'])
            product_before_update = product_before_update_dict.get(product['id'])
            if product_before_update:
                stock_id = product['stock_list__id']
                diff = {
                    field: {"Previous": str(product_before_update[field]), "New": str(updated_value)}
                    for field, updated_value in product.items()
                    if updated_value != product_before_update.get(field)
                }

                changes = ''
                if diff:
                    for key, value in diff.items():
                        if key == 'order_mode':
                            changes += f'{key}: {get_enum_key_by_value(AllowOrderFrom, int(value["Previous"]))} -> {get_enum_key_by_value(AllowOrderFrom, int(value["New"]))}'
                        else:
                            changes += f'\n {key}: {value["Previous"]} -> {value["New"]},'
                    _now = datetime.datetime.now()

                    changes_to_be_created.append(
                        ProductChangesLogs(
                            product_id=product["id"],
                            is_salesable=diff.get("is_salesable"),
                            is_published=diff.get("is_published"),
                            order_mode=diff.get("order_mode"),
                            is_flash_item=diff.get("is_flash_item"),
                            trading_price=diff.get("trading_price"),
                            discount_rate=diff.get("discount_rate"),
                            entry_by_id=request.user.id,
                            organization=request.user.organization,
                            updated_at=_now,
                            date=_now,
                        )
                    )

                    message += f'\n Product: **{product["full_name"]}** (ID: #{product["id"]}) (Stock ID: #{stock_id}).\n Changes: {changes}'

        ProductChangesLogs.objects.bulk_create(changes_to_be_created, batch_size=1000)
        # Update stock document
        stock_qs = Stock().get_all_actives().filter(
            pk__in=product_updated_related_stock_id_list
        )
        update_stock_es_doc(queryset=stock_qs)
        send_message_to_mattermost_by_channel_id(
            channel_id=channel_id,
            message=message,
        )

        return Response({"detail": _("SUCCESSFULLY_UPDATED")}, status=status.HTTP_200_OK)


class ProductListFetchByStockId(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        IsSuperUser,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission, )
    serializer_class = ProductModelSerializer.ProductListFetchByStockId
    filterset_class = ProductFilter
    pagination_class = None

    def get_queryset(self, related_fields=None, only_fields=None):
        filters_params = self.request.query_params
        stock_ids = self.request.query_params.get("stock_ids", "")
        stock_ids = stock_ids.split(",")
        stock_ids = list(
            filter(lambda item: checkers.is_integer(item), stock_ids)
        )
        # Return empty is no filter passed
        if not bool(filters_params):
            return Product.objects.none()
        stock_qs = Stock().get_all_actives().only("id", "product_id", "is_ad_enabled", "priority")
        queryset = super().get_queryset(related_fields, only_fields)
        # Order by stock ids
        preserved = Case(*[When(stock_list=pk, then=pos) for pos, pk in enumerate(stock_ids)])
        queryset = queryset.filter(
            is_salesable=True
        ).select_related(
            "form",
        ).prefetch_related(
            Prefetch(
            "stock_list",
            queryset=stock_qs,
        )
        ).only(
            "id",
            "alias",
            "name",
            "strength",
            "trading_price",
            "discount_rate",
            "form",
            "form__name",
            "is_published",
            "is_flash_item",
            "is_salesable",
            "order_mode",
            "stock_list",
            "stock_list__is_ad_enabled",
            "stock_list__priority",
            "minimum_order_quantity",
        ).order_by(preserved)

        return queryset


class DamageProductList(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        IsSuperUser,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = DamageProductListSerializer

    def get_queryset(self):
        type_ = self.request.query_params.get("type", None)
        queryset = (
            Damage()
            .get_all_actives()
            .select_related(
                "invoice_group",
                "reported_by",
            )
        )
        if type_:
            queryset = queryset.filter(damage_io__type=type_)

        return queryset


class DamageProductDetail(RetrieveUpdateDestroyAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        IsSuperUser,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = DamageProductDetailSerializer
    lookup_field = "alias"

    def get_queryset(self):
        return Damage().get_all_actives()

    def get_object(self):
        alias = self.kwargs.get("alias", None)
        return get_object_or_404(Damage.objects.filter(), alias=alias)


class RecheckProductList(ListCreateAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        IsSuperUser,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = RecheckProductListSerializer

    def get_queryset(self):
        type_ = self.request.query_params.get("type", None)
        top_sheet = self.request.query_params.get("top_sheet", None)
        invoice = self.request.query_params.get("invoice_group", None)
        is_approved = self.request.query_params.get("is_approved", False)

        queryset = (
            Recheck().get_all_actives().select_related("rechecked_by", "invoice_group")
        )
        if type_:
            queryset = queryset.filter(recheck_io__type=type_)

        if top_sheet:
            queryset = queryset.filter(top_sheet=top_sheet)

        if is_approved:
            queryset = queryset.filter(recheck_io__is_approved=True)

        if invoice:
            queryset = queryset.filter(recheck_io__invoice_group=invoice)

        return queryset


class RecheckProductDetail(RetrieveUpdateDestroyAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        IsSuperUser,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = RecheckProductDetailSerializer
    lookup_field = "alias"

    def get_queryset(self):
        return Recheck().get_all_actives()


class DamageItemsList(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        IsSuperUser,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = DamageItemsSerializer
    filterset_class = DamageItemFilter

    def get_queryset(self):
        return (
            DamageProduct()
            .get_all_actives()
            .select_related(
                "damage",
                "stock",
                "invoice_group",
            )
        )


"""
    Recheck products
        - list of items
"""


class RecheckItemsList(ListAPICustomView):
    available_permission_classes = (
        StaffIsAdmin,
        IsSuperUser,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = RecheckProductsSerializer

    def get_queryset(self):
        type_ = self.request.query_params.get("type", None)
        top_sheet = self.request.query_params.get("top_sheet", None)
        invoice = self.request.query_params.get("invoice_group", None)
        is_approved = self.request.query_params.get("is_approved", False)

        queryset = (
            RecheckProduct()
            .get_all_actives()
            .select_related(
                "recheck",
                "stock",
                "invoice_group",
                "approved_by",
            )
        )
        if type_:
            queryset = queryset.filter(type=type_)

        if top_sheet:
            queryset = queryset.filter(recheck__top_sheet=top_sheet)

        if is_approved:
            queryset = queryset.filter(is_approved=True)

        if invoice:
            queryset = queryset.filter(invoice_group=invoice)

        return queryset


class RecheckItemsDetail(generics.RetrieveDestroyAPIView):
    available_permission_classes = (
        StaffIsAdmin,
        IsSuperUser,
        StaffIsProcurementManager,
    )
    permission_classes = (CheckAnyPermission,)
    serializer_class = RecheckProductsSerializer
    lookup_field = "alias"
    queryset = (
        RecheckProduct()
        .get_all_actives()
        .select_related(
            "recheck",
            "stock",
            "invoice_group",
            "approved_by",
        )
    )
