import logging
import os
from decimal import Decimal
from datetime import datetime, timedelta
from dotmap import DotMap
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Case, When, Subquery, F, CharField, BooleanField, Q, Count, Sum
from django.db.models.functions import Coalesce
from django.db.models import (
    Case, When, Subquery, F, CharField,
    BooleanField, Q, Count, Sum,
)

from common.cache_keys import (
    TRENDING_STOCK_PK_LIST_CACHE_KEY,
    TOP_MANUFACTURING_COMPANY_PK_LIST_CACHE_KEY,
    TOP_SOLD_STOCKS_PK_LIST_CACHE_KEY,
    DELIVERY_AREA_HUB_ID_CACHE_KEY,
    DELIVERY_COUPON_STOCK_CACHE_KEY_PREFIX,
    CUSTOMER_ORG_NON_GROUP_ORDER_GRAND_TOTAL_CACHE_KEY_PREFIX,
    CUSTOMER_ORG_DELIVERY_COUPON_AVAILABILITY_CACHE_KEY_PREFIX,
    ORG_CUMULATIVE_DISCOUNT_FACTOR_VALUE_CACHE_KEY,
    ORG_INSTANCE_CACHE_KEY_PREFIX,
    PRODUCT_GENERIC_NULL_NAME_ID_CACHE_KEY,
    ORGANIZATION_AND_AREA_DISCOUNT_CACHE_KEY,
    ORGANIZATION_HAS_ORDER_ON_DELIVERY_DATE,
)
from common.enums import Status
from common.utils import Round
from common.cache_helpers import (
    get_or_clear_cumulative_discount_factor,
    set_or_clear_delivery_date_cache,
)

from core.enums import AllowOrderFrom
from core.models import OrganizationSetting, DeliveryHub, Organization
from pharmacy.models import Stock, StockIOLog, ProductGeneric
from pharmacy.enums import DistributorOrderType, PurchaseType, OrderTrackingStatus
from pharmacy.enums import DistributorOrderType, PurchaseType
from pharmacy.models import Stock, StockIOLog, Purchase
from pharmacy.enums import DistributorOrderType, PurchaseType, OrderTrackingStatus
from pharmacy.custom_serializer.stock import DistributorSalesableStock
from pharmacy.utils import get_delivery_date_for_product

logger = logging.getLogger(__name__)

class HealthOSHelper:

    def trending_products_pk_list_cache_key(self):
        return TRENDING_STOCK_PK_LIST_CACHE_KEY

    def top_manufacturing_company_pk_list_cache_key(self):
        return TOP_MANUFACTURING_COMPANY_PK_LIST_CACHE_KEY

    def top_sold_stocks_pk_list_cache_key(self):
        return TOP_SOLD_STOCKS_PK_LIST_CACHE_KEY

    def delivery_area_hub_id_cache_key(self):
        return DELIVERY_AREA_HUB_ID_CACHE_KEY

    def product_generic_null_name_id_cache_key(self):
        return PRODUCT_GENERIC_NULL_NAME_ID_CACHE_KEY

    @staticmethod
    def get_trending_products_pk_list():
        cls = HealthOSHelper()
        return cls.get_trending_products_pk_list_cache()

    def get_trending_products_pk_list_cache(self):
        cached_data = cache.get(self.trending_products_pk_list_cache_key())
        if cached_data is not None:
            return cached_data
        data_from_db = self.get_trending_products_pk_list_db()
        self.set_trending_products_pk_list_cache(data_from_db)
        return data_from_db

    def get_trending_products_pk_list_db(self):
        hours = 24
        max_items = 50
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
        ).order_by('-unique_pharmacy_order_count'))[:max_items]
        return trending_items_pk_list

    def set_trending_products_pk_list_cache(self, data):
        cache_timeout = 1800
        cache.set(self.trending_products_pk_list_cache_key(), data, timeout=cache_timeout)

    def base_stock_queryset(self):
        healthos_settings = self.settings()
        queryset = Stock.objects.filter(
            status=Status.ACTIVE,
            organization__id=self.organization_id(),
            store_point__id=self.store_point_id(),
            product__is_published=True,
            product__order_limit_per_day__gt=0,
            product__is_salesable=True
        )
        if healthos_settings.allow_order_from == AllowOrderFrom.STOCK and not healthos_settings.overwrite_order_mode_by_product:
            queryset = queryset.exclude(product__is_queueing_item=True)
        elif healthos_settings.overwrite_order_mode_by_product:
            queryset = queryset.exclude(
                product__is_queueing_item=True,
                product__order_mode=AllowOrderFrom.STOCK
            )
        return queryset

    @staticmethod
    def settings():
        from common.utils import get_healthos_settings
        return get_healthos_settings()

    @staticmethod
    def organization_id():
        distributor_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
        try:
            return int(distributor_id)
        except:
            return distributor_id

    @staticmethod
    def store_point_id():
        default_store_point_id = 408
        return default_store_point_id

    def get_top_manufacturing_company_pk_list_db(self):
        stocks = self.base_stock_queryset()
        default_org_setting = OrganizationSetting.objects.filter(
            organization__id=self.organization_id()
        ).only('overwrite_order_mode_by_product', 'allow_order_from')
        overwrite_order_mode_by_product = default_org_setting.values_list(
            'overwrite_order_mode_by_product', flat=True
        )
        allow_order_from = default_org_setting.values_list(
            'allow_order_from', flat=True
        )
        stocks = stocks.filter(
            is_salesable=True,
            product__is_queueing_item=False,
        ).annotate(
            org_order_mode=Subquery(
                overwrite_order_mode_by_product[:1],
                output_field=BooleanField()
            ),
            org_allow_order_from=Subquery(
                allow_order_from[:1],
                output_field=CharField()
            ),
            order_mode=Case(
                When(
                    org_order_mode=True,
                    then=F('product__order_mode')
                ),
                default=F('org_allow_order_from'),
                output_field=CharField()
            )
        ).exclude(
            Q(orderable_stock__lte=0) & Q(order_mode=AllowOrderFrom.STOCK)
        )
        stocks = stocks.values(
            "product__manufacturing_company_id"
        ).annotate(product_count=Count("id")).order_by("-product_count")
        company_pk_list = stocks.values_list("product__manufacturing_company_id", flat=True)
        return list(company_pk_list)

    def set_top_manufacturing_company_pk_list_cache(self, data):
        cache_timeout = 1800
        cache.set(
            self.top_manufacturing_company_pk_list_cache_key(),
            data,
            timeout=cache_timeout
        )

    @staticmethod
    def get_top_manufacturing_company_pk_list():
        cls = HealthOSHelper()
        return cls.get_top_manufacturing_company_list_pk_cache()

    def get_top_manufacturing_company_list_pk_cache(self):
        cached_data = cache.get(self.top_manufacturing_company_pk_list_cache_key())
        if cached_data:
            return cached_data
        data_from_db = self.get_top_manufacturing_company_pk_list_db()
        self.set_top_manufacturing_company_pk_list_cache(data_from_db)
        return data_from_db

    @staticmethod
    def get_top_sold_stocks_pk_list():
        cls = HealthOSHelper()
        return cls.get_top_sold_stocks_pk_list_cache()

    def get_top_sold_stocks_pk_list_cache(self):
        cached_data = cache.get(self.top_sold_stocks_pk_list_cache_key())
        if cached_data is not None:
            return cached_data
        data_from_db = self.get_top_sold_stocks_pk_list_db()
        self.set_top_sold_stocks_pk_list_cache(data_from_db)
        return data_from_db

    def get_top_sold_stocks_pk_list_db(self):
        days = 90
        max_items = 1000
        start_date_time = timezone.make_aware(
            datetime.now(), timezone.get_current_timezone()
        ) - timedelta(days=days)
        end_date_time = timezone.make_aware(datetime.now(), timezone.get_current_timezone())
        top_sold_stocks_pk_list = list(StockIOLog.objects.filter(
            status=Status.DISTRIBUTOR_ORDER,
            purchase__status=Status.DISTRIBUTOR_ORDER,
            purchase__distributor_order_type=DistributorOrderType.ORDER,
            purchase__purchase_type=PurchaseType.VENDOR_ORDER,
            purchase__purchase_date__range=[start_date_time, end_date_time]
        ).exclude(
            purchase__current_order_status__in=[OrderTrackingStatus.CANCELLED, OrderTrackingStatus.REJECTED]
        ).values_list("stock_id", flat=True).annotate(
            stock_quantity_sum=Sum("quantity"),
        ).order_by("-stock_quantity_sum"))[:max_items]

        return top_sold_stocks_pk_list

    def set_top_sold_stocks_pk_list_cache(self, data):
        # Set cache timeout to 24 hours that is 86400 seconds
        cache_timeout = 86400
        cache.set(self.top_sold_stocks_pk_list_cache_key(), data, timeout=cache_timeout)

    @staticmethod
    def get_delivery_area_hub_id_list():
        cls = HealthOSHelper()
        return cls.get_delivery_area_hub_id_list_cache()

    def get_delivery_area_hub_id_list_cache(self):
        cached_data = cache.get(self.delivery_area_hub_id_cache_key())
        if cached_data is not None:
            return cached_data
        data_from_db = self.get_delivery_area_hub_id_list_db()
        self.set_delivery_area_hub_id_list_cache(data_from_db)
        return data_from_db

    def get_delivery_area_hub_id_list_db(self):
        delivery_hubs = DeliveryHub().get_all_actives().only("id", "hub_areas")
        # Create a dictionary to store the area code to hub_id mapping
        delivery_area_hub_id = {}
        # Iterate over the queryset and populate the dictionary
        for delivery_hub in delivery_hubs:
            delivery_hub_id = delivery_hub.id
            # Get all the areas of the delivery hub
            hub_areas = delivery_hub.hub_areas
            for area in hub_areas:
                delivery_area_hub_id[str(area)] = delivery_hub_id

        return delivery_area_hub_id

    def set_delivery_area_hub_id_list_cache(self, data):
        # Set cache timeout to 7 days that is 604800 seconds
        cache_timeout = 604800
        cache.set(self.delivery_area_hub_id_cache_key(), data, timeout=cache_timeout)

    @staticmethod
    def get_delivery_coupon_stock_data():
        cls = HealthOSHelper()
        return cls.get_delivery_coupon_stock_data_from_cache()

    @staticmethod
    def get_delivery_coupon_stock_id():
        stock_id_from_env = os.getenv("EXPRESS_DELIVERY_STOCK_ID", None)
        return int(stock_id_from_env) if stock_id_from_env is not None else None

    def get_delivery_coupon_stock_data_from_cache(self):
        cached_data = cache.get(DELIVERY_COUPON_STOCK_CACHE_KEY_PREFIX)
        if cached_data is not None:
            return cached_data
        delivery_coupon_stock_id = os.getenv("EXPRESS_DELIVERY_STOCK_ID", None)
        try:
            delivery_coupon_stock_instance = Stock.objects.get(pk=delivery_coupon_stock_id)
            serialized_data = DotMap(DistributorSalesableStock.ListForSuperAdmin(delivery_coupon_stock_instance).data)
            cache_timeout = 86400
            cache.set(DELIVERY_COUPON_STOCK_CACHE_KEY_PREFIX, serialized_data, cache_timeout)
            return serialized_data
        except:
            raise ValueError("No Stock id found in Env for delivery coupon.")

    def get_delivery_coupon_price(self):
        """Get the delivery coupon price

        Returns:
            float: current price of the delivery coupon
        """
        try:
            price = self.get_delivery_coupon_stock_data_from_cache().product.trading_price
            return price
        except KeyError:
            return 0

    @staticmethod
    def get_null_name_product_generic_pk_list():
        cls = HealthOSHelper()
        return cls.get_null_name_product_generic_pk_list_cache()

    def get_null_name_product_generic_pk_list_cache(self):
        cached_data = cache.get(self.product_generic_null_name_id_cache_key())
        if cached_data:
            return cached_data
        data_from_db = self.get_null_name_product_generic_pk_list_db()
        self.set_null_name_product_generic_pk_list_cache(data_from_db)
        return data_from_db

    def get_null_name_product_generic_pk_list_db(self):
        product_generic_pk_list = list(
            ProductGeneric.objects.filter(
                Q(name__isnull=True) | Q(name="N/A")
            ).values_list("id", flat=True)
        )
        return product_generic_pk_list

    def set_null_name_product_generic_pk_list_cache(self, data):
        cache_timeout = 1800
        cache.set(self.product_generic_null_name_id_cache_key(), data, timeout=cache_timeout)


class CustomerHelper:

    """Customer related helpers
    """
    def __init__(self, organization_id):
        self.organization_id = organization_id

    def get_non_group_total_amount_for_regular_and_pre_order(self):
        """Calculate total order amount(grand total) for a specific delivery date the orders
        aren't grouped yet

        Returns:
            float: total order amount for a specific delivery date(regular / pre order)
        """
        return (
            self.get_non_group_total_amount_for_regular_or_pre_order_from_cache(is_pre_order=True) +
            self.get_non_group_total_amount_for_regular_or_pre_order_from_cache(is_pre_order=False)
        )

    def get_non_group_total_amount_for_regular_order(self):
        """Total non grouped order amount for regular order

        Returns:
            float: total order amount
        """
        return self.get_non_group_total_amount_for_regular_or_pre_order_from_cache(is_pre_order=False)

    def get_non_group_total_amount_for_pre_order(self):
        """Total non grouped order amount for pre order

        Returns:
            float: total order amount
        """
        return self.get_non_group_total_amount_for_regular_or_pre_order_from_cache(is_pre_order=True)

    def get_non_group_total_amount_for_regular_or_pre_order_from_cache(self, is_pre_order=False, delivery_date=""):
        """Calculate order grad total for a specific delivery date or return from cache

        Args:
            is_pre_order (bool, optional): define pre order or regular order to get the delivery date. Defaults to False.
            delivery_date (str(2023-10-25), optional): this date will get the coupon for the provided date. Defaults to blank.

        Returns:
            float: order grand total amount
        """
        if not delivery_date:
            delivery_date = get_delivery_date_for_product(is_queueing_item=is_pre_order)
        cache_key = f"{CUSTOMER_ORG_NON_GROUP_ORDER_GRAND_TOTAL_CACHE_KEY_PREFIX}_{self.organization_id}_{delivery_date}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        order_grand_total = Purchase.objects.filter(
            organization_id=self.organization_id,
            tentative_delivery_date=delivery_date,
            status=Status.DISTRIBUTOR_ORDER,
            distributor_order_type=DistributorOrderType.ORDER,
            purchase_type=PurchaseType.VENDOR_ORDER,
            current_order_status__in=[
                OrderTrackingStatus.PENDING,
                OrderTrackingStatus.ACCEPTED,
                OrderTrackingStatus.IN_QUEUE
            ],
            invoice_group__isnull=True
        ).aggregate(
            amount_total=Coalesce(Round(Sum('amount') - Sum('discount') + Sum('round_discount')), 0.00)
        ).get('amount_total', 0)
        cache_timeout = 3600
        cache.set(cache_key, order_grand_total, cache_timeout)
        return order_grand_total

    def get_delivery_coupon_availability_for_regular_order(self):
        """Total non grouped order amount for regular order

        Returns:
            float: total order amount
        """
        return self.get_delivery_coupon_availability_for_regular_or_pre_order_from_cache(is_pre_order=False)

    def get_delivery_coupon_availability_for_pre_order(self):
        """Total non grouped order amount for pre order

        Returns:
            float: total order amount
        """
        return self.get_delivery_coupon_availability_for_regular_or_pre_order_from_cache(is_pre_order=True)

    def get_delivery_coupon_availability_for_regular_or_pre_order_from_cache(self, is_pre_order=False, delivery_date=""):
        """Get to know if an org already have an delivery coupon for a delivery date

        Args:
            is_pre_order (bool, optional): define pre order or regular order to get the delivery date. Defaults to False.
            delivery_date (str(2023-10-25), optional): this date will get the coupon for the provided date. Defaults to blank.

        Returns:
            bool: an org already have a delivery coupon or not
        """
        if not delivery_date:
            delivery_date = get_delivery_date_for_product(is_queueing_item=is_pre_order)
        cache_key = f"{CUSTOMER_ORG_DELIVERY_COUPON_AVAILABILITY_CACHE_KEY_PREFIX}_{self.organization_id}_{delivery_date}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        heath_os_helper = HealthOSHelper()
        coupon_stock_id = heath_os_helper.get_delivery_coupon_stock_id()
        coupon_qs = StockIOLog.objects.filter(
            organization_id=self.organization_id,
            status=Status.DISTRIBUTOR_ORDER,
            stock_id=coupon_stock_id,
            purchase__tentative_delivery_date=delivery_date,
            purchase__distributor_order_type=DistributorOrderType.ORDER,
            purchase__purchase_type=PurchaseType.VENDOR_ORDER,
            purchase__current_order_status__in=[
                OrderTrackingStatus.PENDING,
                OrderTrackingStatus.ACCEPTED,
                OrderTrackingStatus.IN_QUEUE
            ],
            purchase__invoice_group__isnull=True
        )
        is_coupon_available = coupon_qs.exists()
        cache_timeout = 3600
        cache.set(cache_key, is_coupon_available, cache_timeout)
        return is_coupon_available


    def get_cumulative_discount_factor(self):
        """
        Retrieve or calculate the cumulative discount factor for an organization.

        Args:
        - organization_id (int): The ID of the organization.

        Returns:
        - Decimal: The cumulative discount factor value for the organization.
        """
        # Check if discount factor enabled for this org or not
        # Return 0 if discount factor is not enabled
        org_instance = self.get_organization_data()
        if not org_instance.has_dynamic_discount_factor:
            return Decimal(0)
        # Attempt to retrieve from cache
        cumulative_discount_factor = get_or_clear_cumulative_discount_factor(
            organization_id=self.organization_id
        )

        if cumulative_discount_factor is not None:
            # If found in cache, return and indicate
            logger.info(
                f"Cumulative discount factor for organization {self.organization_id} found in cache"
            )
            return cumulative_discount_factor

        # If not found in cache, proceed with query
        # Retrieve organization details
        organization = org_instance
        area_discount_factor = organization.area.discount_factor if organization.area_id else Decimal(0)

        # Calculate cumulative discount factor
        cumulative_discount_factor = organization.discount_factor + area_discount_factor
        logger.info(
            f"for organization id: {self.organization_id} cumulative_discount_factor: \
                {cumulative_discount_factor} calculated from DB!"
        )
        # Set the value in the cache
        cache_key = f"{ORG_CUMULATIVE_DISCOUNT_FACTOR_VALUE_CACHE_KEY}{self.organization_id}"
        cache.set(key=cache_key, value=cumulative_discount_factor)

        return cumulative_discount_factor

    def get_organization_data(self):
        """
        Retrieve organization data from the cache database
        """

        cache_key = f"{ORG_INSTANCE_CACHE_KEY_PREFIX}{self.organization_id}"
        # Get from cache
        org_data = cache.get(key=cache_key)
        if org_data is not None:
            return org_data
        # Retrieve organization details
        try:
            # Get instance from DB
            organization = Organization().get_all_actives().get(id=self.organization_id)
            # Set cache for 7 days
            cache.set(key=cache_key, value=organization, timeout=604800)
            return organization
        except Organization.DoesNotExist:
            return None

    def has_dynamic_discount_factor(self):
        """
        Check if the organization has dynamic discount factor
        """

        return self.get_organization_data().has_dynamic_discount_factor

    def get_organization_and_area_discount(self):
        """
        Retrieve organization and area discount factors.
        This method fetches the organization and area discount factors from the database.
        If the data is not found in the cache, it retrieves it from the database and caches it for future use.
        Returns:
        dict: A dictionary containing 'organization_discount_factor' and 'area_discount_factor'.
        """
        # Check if discount factor enabled for this org or not
        # Return 0 if discount factor is not enabled
        org_instance = self.get_organization_data()

        if not org_instance.has_dynamic_discount_factor:
            organization_area_discount_data = {
                "organization_discount_factor": Decimal(0.00),
                "area_discount_factor": Decimal(0.00)
            }
            return organization_area_discount_data

        # Create a unique cache key based on the organization ID
        cache_key = ORGANIZATION_AND_AREA_DISCOUNT_CACHE_KEY + str(self.organization_id)
        # Attempt to retrieve data from the cache
        organization_area_discount_data = cache.get(cache_key, None)
        if organization_area_discount_data is None:
            # Data not found in the cache, fetch from the database
            organization_area_discount = Organization.objects.values(
                "discount_factor",
                "area__discount_factor",
            ).get(
                id=self.organization_id
            )
            organization_area_discount_data = {
                "organization_discount_factor": organization_area_discount.get("discount_factor", 0.00),
                "area_discount_factor": organization_area_discount.get("area__discount_factor", 0.00)
            }

            # Checking if area discount factor is None
            if organization_area_discount_data["area_discount_factor"] is None:
                organization_area_discount_data["area_discount_factor"] = Decimal(0.00)

            # store the data in the cache
            cache.set(cache_key, organization_area_discount_data)
            # return the data
            return organization_area_discount_data

        # Data found in the cache, return cached data
        return organization_area_discount_data


    def has_delivery_on_date(self, delivery_date):
        """
        Checks if there is a delivery scheduled for a specific date for the organization.

        Args:
        - delivery_date (datetime): The date of the delivery.

        Returns:
        - bool: True if there is a delivery scheduled for the provided date, otherwise False.
        """

        # Create keys for caching delivery dates specific to the organization
        delivery_date_key = f"{ORGANIZATION_HAS_ORDER_ON_DELIVERY_DATE}{str(delivery_date)}_{self.organization_id}"

        # Retrieve from the cache
        data = cache.get(key=delivery_date_key)
        if data is not None:
            return data
        # Populate cache if not found
        set_or_clear_delivery_date_cache(
            organization_id=self.organization_id,
            delivery_date=delivery_date
        )
        # Recursive call for getting the result
        return self.has_delivery_on_date(delivery_date=delivery_date)


    def is_order_allowed(self, delivery_date, total_amount):
        """
        Checks if an order is allowed for the organization based on the delivery date and total amount.

        Args:
        - delivery_date (datetime): The date of the delivery.
        - total_amount (float): The total amount of the order.

        Returns:
        - bool: True if the order is allowed based on the criteria, otherwise False.
        """

        min_order_amount = self.get_organization_data().min_order_amount

        has_delivery = self.has_delivery_on_date(delivery_date=delivery_date)

        # Check if there is a delivery on the date or if the total amount is greater than the minimum order amount
        if has_delivery or total_amount >= min_order_amount:
            return True
        return False
