import os, logging
import time, decimal
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models.functions import Cast
from django.db.models import (
    Func,
    IntegerField,
    Value,
    Sum,
    F
)
from django.core.cache import cache
from django.contrib.postgres.aggregates import ArrayAgg
from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import(
    ListSerializer
)
from common.custom_serializer_field import UUIDRelatedField
from common.serializers import DynamicFieldsModelSerializer
from common.enums import Status
from common.helpers import (
    custom_elastic_rebuild
)
from common.cache_keys import (
    CUSTOMER_ORG_NON_GROUP_ORDER_GRAND_TOTAL_CACHE_KEY_PREFIX,
    CUSTOMER_ORG_DELIVERY_COUPON_AVAILABILITY_CACHE_KEY_PREFIX,
)
from common.healthos_helpers import HealthOSHelper, CustomerHelper
from pharmacy.utils import (
    delete_order_list_from_cache,
    get_next_valid_delivery_date,
)
from pharmacy.tasks import remove_delivery_coupon_lazy

from core.serializers import PersonOrganizationEmployeeSearchSerializer
from core.custom_serializer.organization import OrganizationModelSerializer

from pharmacy.enums import (
    OrderTrackingStatus,
    PurchaseType,
    DistributorOrderType,
)
from pharmacy.models import Purchase
from pharmacy.custom_serializer.purchase import (
    OrderStockIOForInvoiceGroupSerializer,
    OrderStockIOForInvoiceGroupPDFSerializer,
)
from expo_notification.tasks import send_push_notification_to_mobile_app_by_org

from ecommerce.tasks import (
    update_es_index_for_related_invoices,
    update_invoice_groups_additional_discount_based_on_delivery_date,
)
from ecommerce.helpers import send_delayed_delivery_message_to_mm
from ecommerce.utils import (
    is_last_batch_invoice_group,
)
from ..models import OrderInvoiceGroup, ShortReturnLog, ShortReturnItem

logger = logging.getLogger(__name__)
class Round(Func):
    function = "ROUND"
    template = "%(function)s(%(expressions)s::numeric, 3)"


class OrderInvoiceGroupMeta(ListSerializer.Meta):
    model = OrderInvoiceGroup
    fields = ListSerializer.Meta.fields + (
        'date',
        'delivery_date',
        'sub_total',
        'discount',
        'round_discount',
        'current_order_status',
        'responsible_employee',
        'additional_discount',
        'additional_discount_rate',
        'additional_cost',
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
        # read only fields can be added here
    )


class OrderInvoiceGroupModelSerializerBase:

    class Post(serializers.Serializer):

        delivery_date = serializers.DateField()
        current_order_status = serializers.ChoiceField(choices=OrderTrackingStatus().choices())

        class Meta:
            model = OrderInvoiceGroup

        def delete_customer_non_group_order_amount_cache(self, keys):
            cache.delete_many(keys)

        def populate_es_index(self, invoice_pk_list):
            _chunk_size = 30
            _number_of_operation = int((len(invoice_pk_list) / _chunk_size) + 1)

            _lower_limit = 0
            _upper_limit = _chunk_size
            for _ in range(0, _number_of_operation):
                pks = list(invoice_pk_list[_lower_limit:_upper_limit])
                custom_elastic_rebuild(
                    'ecommerce.models.OrderInvoiceGroup',
                    {'pk__in': pks}
                )
                update_es_index_for_related_invoices.apply_async(
                    (pks, ),
                    countdown=5,
                    retry=True, retry_policy={
                        'max_retries': 10,
                        'interval_start': 0,
                        'interval_step': 0.2,
                        'interval_max': 0.2,
                    }
                )
                _lower_limit = _upper_limit
                _upper_limit = _lower_limit + _chunk_size

        @transaction.atomic
        def create(self, validated_data):
            from ecommerce.invoice_pdf_helpers import create_invoice_pdf_on_invoice_group_create_lazy
            try:
                health_os_helper = HealthOSHelper()
                # Current Price of the Delivery Coupon
                delivery_coupon_price = health_os_helper.get_delivery_coupon_price()
                request = self.context.get("request")
                DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
                _datetime_now = datetime.strptime(
                    time.strftime(DATE_TIME_FORMAT, time.localtime()), DATE_TIME_FORMAT)
                _delivery_date = validated_data.get('delivery_date')
                filters = {
                    "status": Status.DISTRIBUTOR_ORDER,
                    "distributor_order_type": DistributorOrderType.ORDER,
                    "purchase_type": PurchaseType.VENDOR_ORDER,
                    "tentative_delivery_date": _delivery_date,
                    "current_order_status": validated_data.get('current_order_status'),
                    "distributor__id": request.user.organization_id,
                    "invoice_group__isnull": True
                }

                orders = Purchase.objects.filter(**filters).values('organization').annotate(
                    order_ids=ArrayAgg(Cast('pk', IntegerField()), distinct=True),
                    sum_amount=Round(Sum(F('amount'))),
                    sum_discount=Round(Sum(F('discount'))),
                    sum_round_discount=Round(Sum(F('round_discount'))),
                    sum_grand_total=Round(Sum(F('grand_total'))),
                    sum_additional_discount=Round(Sum(F('additional_discount'))),
                    sum_additional_cost=Round(Sum(F('additional_cost'))),
                    sum_dynamic_discount_amount_total=Round(Sum(F('dynamic_discount_amount'))),
                    org_min_order_amount=F('organization__min_order_amount'),
                )
                orders = list(orders)

                data_list = []
                customer_non_group_order_amount_cache_keys = []
                invoice_group_pk_list = []
                invoice_group_date_list = []
                express_delivery_stock_id = os.environ.get('EXPRESS_DELIVERY_STOCK_ID', None)
                # Set delivery date based on order closing info
                new_delivery_date = get_next_valid_delivery_date(str(_delivery_date))
                for order in orders:
                    # total order amount for a specific delivery cache and coupon already added cache needed to be expired
                    customer_non_group_order_amount_cache_keys.extend([
                        f"{CUSTOMER_ORG_NON_GROUP_ORDER_GRAND_TOTAL_CACHE_KEY_PREFIX}_{order.get('organization')}_{_delivery_date}",
                        f"{CUSTOMER_ORG_DELIVERY_COUPON_AVAILABILITY_CACHE_KEY_PREFIX}_{order.get('organization')}_{_delivery_date}"
                    ])
                    # Organization id for customer
                    customer_organization_id = order.get('organization')
                    # Calculate additional_dynamic_discount_percentage for invoice
                    sum_dynamic_discount_amount_total = order.get("sum_dynamic_discount_amount_total", 0.00)
                    sum_grand_total = decimal.Decimal(order.get("sum_grand_total", 0.00))
                    grand_total_without_dynamic_discount = sum_grand_total + sum_dynamic_discount_amount_total
                    additional_dynamic_discount_percentage = (sum_dynamic_discount_amount_total * 100) / grand_total_without_dynamic_discount
                    will_create_invoice = True
                    express_delivery_stock_id = None
                    if express_delivery_stock_id is not None:
                        express_delivery_stock_id = int(express_delivery_stock_id)
                        org_min_order_amount = order.get('org_min_order_amount', 0)
                        sum_amount = order.get('sum_amount', 0)
                        sum_discount = order.get('sum_discount', 0)
                        sum_round_discount = order.get('sum_round_discount', 0)
                        sum_total_amount = sum_amount - sum_discount + sum_round_discount
                        order_ids = order.get('order_ids')
                        if sum_total_amount < org_min_order_amount:
                            purchases = Purchase.objects.filter(pk__in=order_ids)
                            purchases_stock_ids = purchases.values_list('stock_io_logs__stock', flat=True)
                            is_express_delivery_exist = express_delivery_stock_id in purchases_stock_ids
                            _is_last_batch_invoice_group = is_last_batch_invoice_group(str(_delivery_date))
                            will_create_invoice = is_express_delivery_exist
                            if not is_express_delivery_exist and _is_last_batch_invoice_group:
                                purchases_ids = purchases.values_list('pk', flat=True)
                                purchases_to_be_updated = []
                                for purchase in purchases_ids:
                                    purchases_to_be_updated.append(
                                        Purchase(
                                            pk=purchase,
                                            updated_by_id=request.user.id,
                                            updated_at=_datetime_now,
                                            tentative_delivery_date=new_delivery_date,
                                            is_delayed=True
                                        )
                                    )
                                Purchase.objects.bulk_update(
                                    purchases_to_be_updated,
                                    ["updated_by", "updated_at", "tentative_delivery_date", "is_delayed"]
                                )
                                # new_delivery_date = str(_delivery_date + timedelta(days=1))
                                organization_orders_str = ", ".join(list(map(lambda order: f"#{order}", purchases_ids)))
                                title = "Delivery Date Updated"
                                body = (
                                    f"Your order amount doesn't meet the minimum limit of ৳{org_min_order_amount:.2f}. "
                                    f"Delivery date for the orders {organization_orders_str} has been changed to {new_delivery_date}. "
                                    f"Add more items to your Bag or select Express Delivery for faster delivery."
                                )

                                # Send push notification
                                send_push_notification_to_mobile_app_by_org.delay(
                                    [order.get('organization')],
                                    title,
                                    body,
                                    {},
                                )

                                # delete previous order ids cache and rebuild the search index for the orders
                                purchases_ids = list(purchases_ids)
                                delete_order_list_from_cache(order_ids)
                                custom_elastic_rebuild(
                                    'pharmacy.models.Purchase',
                                    {'id__in': purchases_ids},
                                )

                                mm_message = (
                                    f"Changed delivery date from {_delivery_date} to {new_delivery_date} "
                                    f"for organization #{order.get('organization', '')} of orders {organization_orders_str}.\n"
                                    f"**Minimum Order Amount:** {org_min_order_amount:.2f}\n"
                                    f"**Total Order Amount:** {round(sum_total_amount):.2f}\n"
                                )
                                send_delayed_delivery_message_to_mm(message=mm_message)
                                continue
                        # Remove coupon if total amount is greater than order limit
                        elif sum_total_amount - delivery_coupon_price > org_min_order_amount:
                            avoud_coupon_remove = False
                            # is_coupon_available = CustomerHelper(customer_organization_id).get_delivery_coupon_availability_for_regular_or_pre_order_from_cache(
                            #     delivery_date=_delivery_date
                            # )
                            # # Remove delivery coupon if available with any order
                            # if is_coupon_available:
                            #     remove_delivery_coupon_lazy.apply_async(
                            #         args=(customer_organization_id, _delivery_date,),
                            #         countdown=3,
                            #         retry=True, retry_policy={
                            #             'max_retries': 10,
                            #             'interval_start': 0,
                            #             'interval_step': 0.2,
                            #             'interval_max': 0.2,
                            #         }
                            #     )
                            #     # Subtract Delivery coupon price from total invoice amount
                            #     order["sum_amount"] -= delivery_coupon_price
                    if will_create_invoice:
                        validated_data['date'] =_datetime_now
                        validated_data['sub_total'] = order.get('sum_amount', 0)
                        validated_data['discount'] = order.get('sum_discount', 0)
                        validated_data['round_discount'] = order.get('sum_round_discount', 0)
                        validated_data['additional_discount'] = order.get('sum_additional_discount', 0)
                        validated_data['additional_discount_rate'] = \
                            order.get('sum_additional_discount', 0) * 100 / (order.get('sum_amount', 0) - \
                            order.get('sum_discount', 0) + order.get('sum_round_discount', 0))
                        validated_data['additional_cost'] = order.get('sum_additional_cost', 0)
                        validated_data['additional_cost_rate'] = \
                            order.get('sum_additional_cost', 0) * 100 / (order.get('sum_amount', 0) - \
                            order.get('sum_discount', 0) + order.get('sum_round_discount', 0))
                        validated_data['order_by_organization_id'] = order.get('organization')
                        validated_data['organization_id'] = request.user.organization_id
                        validated_data['additional_dynamic_discount_percentage'] = additional_dynamic_discount_percentage
                        validated_data['additional_dynamic_discount_amount'] = sum_dynamic_discount_amount_total

                        if not (
                            validated_data.get('entry_by', None) or validated_data.get('entry_by_id', None)
                            ):
                            validated_data['entry_by_id'] = request.user.id

                        instance = OrderInvoiceGroup.objects.create(
                            **validated_data,
                        )
                        data_list.append(instance)
                        invoice_group_pk_list.append(instance.pk)
                        invoice_group_date_list.append(instance.delivery_date.strftime('%Y-%m-%d'))
                        Purchase.objects.filter(pk__in=order.get('order_ids', [])).update(
                            invoice_group_id=instance.id
                        )

                # update_invoice_groups_additional_discount_based_on_delivery_date.apply_async(
                #     (invoice_group_date_list,),
                #     countdown=5,
                #     retry=True, retry_policy={
                #         'max_retries': 10,
                #         'interval_start': 0,
                #         'interval_step': 0.2,
                #         'interval_max': 0.2,
                #     }
                # )
                # Create invoice pdfs using celery
                create_invoice_pdf_on_invoice_group_create_lazy(invoice_group_pk_list, _delivery_date)
                self.populate_es_index(invoice_group_pk_list)
                # delete customer non group order amount cache
                self.delete_customer_non_group_order_amount_cache(
                    customer_non_group_order_amount_cache_keys
                )
                return data_list

            except Exception as exception:
                exception_str = exception.args[0] if exception.args else str(exception)
                # content = {'error': '{}'.format(exception_str)}
                raise serializers.ValidationError(exception_str)

    class List(ListSerializer):
        responsible_employee = PersonOrganizationEmployeeSearchSerializer()
        order_by_organization = OrganizationModelSerializer.LiteWithEntryBy()

        class Meta(OrderInvoiceGroupMeta):
            fields = OrderInvoiceGroupMeta.fields + (
                'responsible_employee',
                'order_by_organization',
                'orders',
                'total_short',
                'total_return',
                'customer_rating',
                'customer_comment',
            )
            read_only_fields = OrderInvoiceGroupMeta.read_only_fields + ()

    class Lite(ListSerializer):

        class Meta(OrderInvoiceGroupMeta):
            fields = OrderInvoiceGroupMeta.fields + (

            )
            read_only_fields = OrderInvoiceGroupMeta.read_only_fields + ()


    class LiteForSearch(ListSerializer):
        responsible_employee = PersonOrganizationEmployeeSearchSerializer()

        class Meta(OrderInvoiceGroupMeta):
            fields = (
                'id',
                'current_order_status',
                'responsible_employee',
            )
            read_only_fields = OrderInvoiceGroupMeta.read_only_fields + ()


    class Details(DynamicFieldsModelSerializer, ListSerializer):
        responsible_employee = PersonOrganizationEmployeeSearchSerializer()
        order_by_organization = OrganizationModelSerializer.LiteWithResponsiblePerson()
        orders = OrderStockIOForInvoiceGroupSerializer(many=True)

        class Meta(OrderInvoiceGroupMeta):
            fields = OrderInvoiceGroupMeta.fields + (
                'additional_discount_rate',
                'additional_cost_rate',
                'responsible_employee',
                'order_by_organization',
                'orders',
                'print_count',
                'customer_rating',
                'customer_comment',
                'additional_dynamic_discount_percentage',
                'additional_dynamic_discount_amount',
            )
            read_only_fields = OrderInvoiceGroupMeta.read_only_fields + (
                'additional_dynamic_discount_percentage',
                'additional_dynamic_discount_amount',
            )


    class DetailsForPDF(ListSerializer):
        order_by_organization = OrganizationModelSerializer.InvoicePDF()
        orders = OrderStockIOForInvoiceGroupPDFSerializer(many=True)

        class Meta(OrderInvoiceGroupMeta):
            fields = OrderInvoiceGroupMeta.fields + (
                'additional_discount_rate',
                'additional_cost_rate',
                'responsible_employee',
                'order_by_organization',
                'orders',
                'additional_dynamic_discount_percentage',
                'additional_dynamic_discount_amount',
                'total_return',
                'total_short',
            )
            read_only_fields = OrderInvoiceGroupMeta.read_only_fields + (
                'additional_dynamic_discount_percentage',
                'additional_dynamic_discount_amount',
            )

    class Update(ListSerializer):

        class Meta(OrderInvoiceGroupMeta):
            fields = OrderInvoiceGroupMeta.fields + (
                'print_count',
            )
            read_only_fields = OrderInvoiceGroupMeta.read_only_fields + ()


    class ForInvoiceGroupDeliverySheetDetails(ListSerializer):
        info = serializers.JSONField()

        class Meta(OrderInvoiceGroupMeta):
            fields = (
                'id',
                'alias',
                'current_order_status',
                'delivery_date',
                'info',
            )
            read_only_fields = OrderInvoiceGroupMeta.read_only_fields + ()

    class StatusResponsiblePersonBulkCreate(serializers.Serializer):
        order_invoice_group_ids = serializers.ListField(
            child=serializers.IntegerField(),
            required=True,
        )
        responsible_employee = serializers.IntegerField(
            required=False,
        )
        remarks = serializers.CharField(
            required=False,
            allow_blank=True,
            allow_null=True,
        )
        current_order_status = serializers.CharField(
            required=False,
            allow_blank=True,
            allow_null=True,
        )

        class Meta:
            fields = (
                'order_invoice_group_ids',
                'responsible_employee',
                'remarks',
                'current_order_status',
            )

class OrderInvoiceGroupModelSerializer(OrderInvoiceGroupModelSerializerBase):

    class Search(OrderInvoiceGroupModelSerializerBase.List):
        related_invoice_groups = OrderInvoiceGroupModelSerializerBase.LiteForSearch(many=True)

        class Meta(OrderInvoiceGroupModelSerializerBase.List.Meta):
            fields = OrderInvoiceGroupModelSerializerBase.List.Meta.fields + (
                'related_invoice_groups',
            )
            read_only_fields = OrderInvoiceGroupMeta.read_only_fields + ()

    class ListWithProductQuantity(OrderInvoiceGroupModelSerializerBase.List):
        total_quantity = serializers.IntegerField()

        class Meta(OrderInvoiceGroupModelSerializerBase.List.Meta):
            fields = OrderInvoiceGroupModelSerializerBase.List.Meta.fields + (
                'total_quantity',
            )
            read_only_fields = OrderInvoiceGroupMeta.read_only_fields + ()

    class StatusReport(ListSerializer):
        delivery_date = serializers.DateField()
        full_name = serializers.CharField()
        porter_code = serializers.CharField()
        assigned_total = serializers.IntegerField()
        accepted = serializers.IntegerField()
        ready_to_deliver = serializers.IntegerField()
        on_the_way = serializers.IntegerField()
        delivered = serializers.IntegerField()
        completed = serializers.IntegerField()
        rejected = serializers.IntegerField()
        cancelled = serializers.IntegerField()
        partial_delivered = serializers.IntegerField()
        full_returned = serializers.IntegerField()
        in_queue = serializers.IntegerField()
        porter_delivered = serializers.IntegerField()
        porter_full_return = serializers.IntegerField()
        porter_partial_delivered = serializers.IntegerField()
        porter_failed_delivered = serializers.IntegerField()
        rating_count = serializers.IntegerField()
        rating_count_of_one = serializers.IntegerField()
        rating_count_of_two = serializers.IntegerField()
        rating_count_of_three = serializers.IntegerField()
        rating_count_of_four = serializers.IntegerField()
        rating_count_of_five = serializers.IntegerField()

        class Meta(OrderInvoiceGroupMeta):
            fields = (
                'delivery_date',
                'full_name',
                'porter_code',
                'assigned_total',
                'accepted',
                'ready_to_deliver',
                'on_the_way',
                'delivered',
                'completed',
                'rejected',
                'cancelled',
                'partial_delivered',
                'full_returned',
                'in_queue',
                'porter_delivered',
                'porter_full_return',
                'porter_partial_delivered',
                'porter_failed_delivered',
                'rating_count',
                'rating_count_of_one',
                'rating_count_of_two',
                'rating_count_of_three',
                'rating_count_of_four',
                'rating_count_of_five',
            )
            read_only_fields = OrderInvoiceGroupMeta.read_only_fields + ()

    class OrderRatingList(ListSerializer):
        class Meta(OrderInvoiceGroupMeta):
            fields = (
                'id',
                'alias'
            )

    class OrderRatingPost(ListSerializer):
        alias = UUIDRelatedField(
            fields=('id', 'alias'),
        )

        class Meta(OrderInvoiceGroupMeta):
            fields = (
                'alias',
                'customer_rating',
                'customer_comment',
            )


class InvoiceGroupProductSumSerializer(serializers.Serializer):
    product_name = serializers.CharField()
    product_sum = serializers.FloatField(read_only=True)
    product_short = serializers.FloatField(read_only=True,)
    product_return = serializers.FloatField(read_only=True)


class InvoiceGroupProductQuantityInvoiceCountSerializer(serializers.Serializer):
    stock_id = serializers.IntegerField(source="stock__id")
    product_name = serializers.CharField()
    company_name = serializers.CharField()
    product_quantity = serializers.IntegerField(read_only=True)
    invoice_count = serializers.IntegerField(read_only=True)
    mrp = serializers.FloatField()
    compartment = serializers.ListField(
        child=serializers.JSONField(),
        read_only=True,
        allow_null=True,
    )

