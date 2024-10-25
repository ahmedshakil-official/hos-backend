import datetime
import json
import os

from django.db.models import (
    Prefetch,
    Q,
    Case,
    F,
    When,
    Sum,
)
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.functions import Coalesce
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from common.enums import Status
from common.helpers import prepare_es_populate_filter as es_filter
from common.utils import get_healthos_settings
from account.models import (
    Transaction,
    TransactionPurchase
)
from pharmacy.models import (
    ProductForm,
    Product,
    ProductManufacturingCompany,
    ProductGroup,
    ProductSubgroup,
    ProductGeneric,
    Purchase,
    ProductCategory,
    ProductDisbursementCause,
    EmployeeStorepointAccess,
    StorePoint,
    Stock,
    StockTransfer,
    Sales,
    StockAdjustment,
    Unit,
)
from pharmacy.enums import PurchaseType, DistributorOrderType
from ..indexes import get_index
from ..fields import CustomDateField
from search.analyzer import html_strip, autocomplete_analyzer
from search.helpers import prepare_stock_document, prepare_image


@registry.register_document
class ProductDocument(Document):
    name = fields.TextField(
        fields={'raw': fields.KeywordField()})
    strength = fields.TextField(
        fields={'raw': fields.KeywordField()})
    full_name = fields.TextField(
        fields={'raw': fields.KeywordField()})
    alias_name = fields.TextField(
        fields={'raw': fields.KeywordField()}
    )
    is_global = fields.IntegerField()
    organization = fields.ObjectField(properties={
        'pk': fields.IntegerField()
    })
    manufacturing_company = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'description': fields.TextField()
    })
    form = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'description': fields.TextField()
    })
    subgroup = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'name': fields.TextField(),
        'description': fields.TextField(),
        'product_group': fields.ObjectField(properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(),
            'description': fields.TextField(),
            'type': fields.IntegerField()
        })
    })
    generic = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'description': fields.TextField()
    })
    status = fields.IntegerField()
    alias = fields.TextField()
    # alias keyword field is for multiple alias search
    alias_keyword = fields.KeywordField()
    primary_unit = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'name': fields.TextField(),
        'description': fields.TextField(),
    })
    secondary_unit = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'name': fields.TextField(),
        'description': fields.TextField(),
    })
    global_category = fields.IntegerField()
    order_mode = fields.IntegerField()
    stock_id = fields.IntegerField()
    # stock_list = fields.ObjectField(properties={
    #     'id': fields.IntegerField(),
    #     'store_point': fields.ObjectField(properties={
    #         'pk': fields.IntegerField(),
    #     }),
    #     'product': fields.ObjectField(properties={
    #         'pk': fields.IntegerField(),
    #     }),
    #     'stock': fields.FloatField()
    # })

    def prepare_alias_keyword(self, instance):
        # return alias to populate alias keyword
        return instance.alias

    def prepare_stock_id(self, instance):
        stock_instance = instance.stock_list.first()
        if stock_instance:
            return stock_instance.id
        return None


    class Index:
        name = get_index('pharmacy_product')._name


    class Django:
        model = Product
        fields = [
            'id',
            'description',
            'trading_price',
            'purchase_price',
            'is_salesable',
            'is_service',
            'conversion_factor',
            'is_published',
            'is_flash_item',
        ]
        queryset_pagination = 1000
        # rebuild_from_value_list = True

    def get_queryset(self, filters={}, orders=['-pk']):
        stocks = Stock.objects.filter(
            status=Status.ACTIVE,
            organization__id=os.environ.get('DISTRIBUTOR_ORG_ID', 303),
        ).only(
            'id',
            'product_id',
        )
        queryset = super(ProductDocument, self).get_queryset().select_related(
            'organization',
            'manufacturing_company',
            'form',
            'subgroup',
            'subgroup__product_group',
            'generic',
        ).filter(
            organization__id=os.environ.get('DISTRIBUTOR_ORG_ID', 303),
            **filters
        ).prefetch_related(
            Prefetch(
                'stock_list',
                queryset=stocks
            )
        ).order_by(*orders)

        return queryset

    # def get_list(self, filter={}):
    #     return Product.objects.extra(select={'pk': 'id'}).values(
    #         'id',
    #         'status',
    #         'is_global',
    #         'name',
    #         'full_name',
    #         'alias',
    #         'strength',
    #         'description',
    #         'trading_price',
    #         'purchase_price',
    #         'is_salesable',
    #         'is_service',
    #         'conversion_factor',
    #         'organization',
    #         'organization__id',
    #         'manufacturing_company',
    #         'manufacturing_company__id',
    #         'manufacturing_company__name',
    #         'manufacturing_company__description',
    #         'form',
    #         'form__id',
    #         'form__name',
    #         'form__description',
    #         'subgroup',
    #         'subgroup__id',
    #         'subgroup__alias',
    #         'subgroup__name',
    #         'subgroup__description',
    #         'subgroup__product_group',
    #         'subgroup__product_group__id',
    #         'subgroup__product_group__name',
    #         'subgroup__product_group__description',
    #         'subgroup__product_group__type',
    #         'generic',
    #         'generic__id',
    #         'generic__name',
    #         'generic__description',
    #         'primary_unit',
    #         'primary_unit__id',
    #         'primary_unit__alias',
    #         'primary_unit__name',
    #         'primary_unit__description',
    #         'secondary_unit',
    #         'secondary_unit__id',
    #         'secondary_unit__alias',
    #         'secondary_unit__name',
    #         'secondary_unit__description',
    #         'global_category',
    #     ).filter(status=Status.ACTIVE).filter(**filter)


@registry.register_document
class ProductFormDocument(Document):
    name = fields.TextField(fields={'raw': fields.KeywordField()})
    status = fields.IntegerField()
    is_global = fields.IntegerField()
    organization = fields.ObjectField(properties={
        'pk': fields.IntegerField()
    })
    alias = fields.TextField()


    class Index:
        name = get_index('pharmacy_product_form')._name


    class Django:
        model = ProductForm
        fields = [
            'id',
            'description'
        ]
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=['-pk']):
        return super(ProductFormDocument, self).get_queryset().select_related(
            'organization',
        ).filter(
            status=Status.ACTIVE
        ).filter(
            **filters
        ).order_by(*orders)


@registry.register_document
class ProductManufacturerDocument(Document):
    name = fields.TextField(fields={'raw': fields.KeywordField()})
    status = fields.IntegerField()
    is_global = fields.IntegerField()
    organization = fields.ObjectField(properties={
        'pk': fields.IntegerField()
    })
    alias = fields.TextField()
    alias_keyword = fields.KeywordField()
    logo =  fields.ObjectField(
        properties={
            "full_size": fields.TextField(),
            "large": fields.TextField(),
            "small": fields.TextField(),
        }
    )

    def prepare_alias_keyword(self, instance):
        return instance.alias

    def prepare_logo(self, instance):
        return prepare_image(
            instance.logo.name,
            "logo_images"
        )


    class Index:
        name = get_index('pharmacy_product_manufacturing_company')._name


    class Django:
        model = ProductManufacturingCompany
        fields = [
            'id',
            'description'
        ]
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=['-pk']):
        return super(ProductManufacturerDocument, self).get_queryset().select_related(
            'organization',
        ).filter(
            status=Status.ACTIVE
        ).filter(
            **filters
        ).order_by(*orders)


@registry.register_document
class ProductGroupDocument(Document):
    name = fields.TextField(fields={'raw': fields.KeywordField()})
    type = fields.IntegerField()
    status = fields.IntegerField()
    is_global = fields.IntegerField()
    organization = fields.ObjectField(properties={
        'pk': fields.IntegerField()
    })
    alias = fields.TextField()
    alias_keyword = fields.KeywordField()

    logo =  fields.ObjectField(
        properties={
            "full_size": fields.TextField(),
            "large": fields.TextField(),
            "small": fields.TextField(),
        }
    )

    def prepare_logo(self, instance):
        return prepare_image(
            instance.logo.name,
            "logo_images"
        )


    def prepare_alias_keyword(self, instance):
        return instance.alias


    class Index:
        name = get_index('pharmacy_product_group')._name


    class Django:
        model = ProductGroup
        fields = [
            'id',
            'description'
        ]
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=['-pk']):
        return super(ProductGroupDocument, self).get_queryset().select_related(
            'organization',
        ).filter(
            status=Status.ACTIVE
        ).filter(
            **filters
        ).order_by(*orders)


@registry.register_document
class ProductSubGroupDocument(Document):
    name = fields.TextField(fields={'raw': fields.KeywordField()})
    status = fields.IntegerField()
    product_group = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.KeywordField(),
        'name': fields.TextField(),
        'description': fields.TextField(),
        'type': fields.IntegerField()
    })
    is_global = fields.IntegerField()
    organization = fields.ObjectField(properties={
        'pk': fields.IntegerField()
    })
    alias = fields.TextField()


    class Index:
        name = get_index('pharmacy_product_sub_group')._name


    class Django:
        model = ProductSubgroup
        fields = [
            'id',
            'description'
        ]
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=['-pk']):
        return super(ProductSubGroupDocument, self).get_queryset().select_related(
            'organization',
            'product_group',
        ).filter(
            status=Status.ACTIVE
        ).filter(
            **filters
        ).order_by(*orders)


@registry.register_document
class ProductGenericDocument(Document):
    name = fields.TextField(fields={'raw': fields.KeywordField()})
    status = fields.IntegerField()
    is_global = fields.IntegerField()
    organization = fields.ObjectField(properties={
        'pk': fields.IntegerField()
    })
    alias = fields.TextField()


    class Index:
        name = get_index('pharmacy_product_generic')._name


    class Django:
        model = ProductGeneric
        fields = [
            'id',
            'description'
        ]
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=['-pk']):
        return super(ProductGenericDocument, self).get_queryset().select_related(
            'organization',
        ).filter(
            status=Status.ACTIVE
        ).filter(
            **filters
        ).order_by(*orders)


@registry.register_document
class PurchaseDocument(Document):
    id = fields.TextField(
        fields={'raw': fields.KeywordField()}
    )
    status = fields.IntegerField()
    purchase_order_status = fields.IntegerField()
    # organization = fields.ObjectField(properties={
    #     'pk': fields.IntegerField()
    # })
    is_sales_return = fields.BooleanField()
    alias = fields.TextField()
    purchase_date = CustomDateField()
    organization_wise_serial = fields.IntegerField()
    person_organization_supplier = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'company_name': fields.TextField(),
        'first_name': fields.TextField(),
        'last_name': fields.TextField(),
        'person_group': fields.IntegerField(),
        'phone': fields.TextField(),
        'opening_balance': fields.FloatField(),
        'email': fields.TextField(fields={'raw': fields.KeywordField()}),
        'full_name': fields.TextField(
            attr='get_full_name', fields={'raw': fields.KeywordField()}),
    })
    amount = fields.DoubleField()
    grand_total = fields.DoubleField()
    person_organization_receiver = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'first_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'last_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'full_name': fields.TextField(
            attr='get_full_name', fields={'raw': fields.KeywordField()}),
        'person_group': fields.IntegerField(),
        'phone': fields.TextField(),
        'code': fields.TextField(),
    })
    department = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'name': fields.TextField(),
        'description': fields.TextField(),
    })
    store_point = fields.ObjectField(
        # attr="get_store_point_of_stock",
        properties={
            'id': fields.IntegerField(),
            'alias': fields.TextField(),
            'name': fields.TextField(),
            'address': fields.TextField(),
            'phone': fields.TextField(),
            'type': fields.IntegerField()
        })
    copied_from = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'vouchar_no': fields.TextField(),
        'organization_wise_serial': fields.IntegerField()
    })
    # requisitions = fields.ObjectField(properties={
    #     'id': fields.IntegerField(),
    #     'alias': fields.TextField(),
    #     'vouchar_no': fields.TextField()

    # })
    pending_amount = fields.DoubleField(
        attr="get_pending_amount"
    )
    transaction_purchase = fields.ObjectField(
        attr="get_transaction_purchase",
        properties={
            'id': fields.IntegerField(),
            'transaction': fields.ObjectField(
                properties={
                    'id': fields.IntegerField(),
                    'organization_wise_serial': fields.IntegerField()
                }
            ),
            'amount': fields.FloatField()
        }
    )
    sales_return = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'copied_from': fields.ObjectField(properties={
                'pk': fields.IntegerField()
            }),
            'organization_wise_serial': fields.IntegerField(),
        }
    )
    purchase_payment = fields.FloatField()
    organization_department = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'alias': fields.TextField(),
            'name': fields.TextField(),
        }
    )
    # Distributor order related fields
    distributor = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'primary_mobile': fields.TextField(),
        'address': fields.TextField()
    })
    distributor_order_group = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'sub_total': fields.FloatField(),
        'discount': fields.FloatField()
    })
    responsible_employee = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'first_name': fields.TextField(),
        'last_name': fields.TextField(),
        'phone': fields.TextField()
    })
    prev_order_date = CustomDateField(attr="prev_order_date")
    order_number_count = fields.IntegerField(attr="order_number_count")
    system_platform = fields.IntegerField()
    distributor_order_type = fields.IntegerField()
    current_order_status = fields.IntegerField()
    purchase_type = fields.IntegerField()
    organization = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(),
            'primary_mobile': fields.TextField(),
            'address': fields.TextField(),
            'delivery_sub_area': fields.TextField(),
            'delivery_thana': fields.IntegerField(),
            'active_issue_count': fields.IntegerField(),
            'entry_by': fields.ObjectField(
                properties={
                    'first_name': fields.TextField(),
                    'last_name': fields.TextField()
                }
            ),
        }
    )
    geo_location_data = fields.ObjectField(dynamic=True)
    is_queueing_order = fields.BooleanField()
    tentative_delivery_date = CustomDateField()
    calculated_profit = fields.FloatField()
    short_total = fields.FloatField(attr="short_total")
    return_total = fields.FloatField(attr="return_total")
    additional_discount = fields.FloatField()

    def prepare_geo_location_data(self, instance):
        geo_data = instance.geo_location_data
        if not geo_data:
            return {}
        if isinstance(geo_data, str):
            json_acceptable_string = geo_data.replace("'", "\"")
            _data = json.loads(json_acceptable_string)
            return _data
        return dict(geo_data)


    class Index:
        name = get_index('pharmacy_purchase')._name


    class Django:
        model = Purchase
        fields = [
            # 'id',
            'remarks',
            'vouchar_no'
        ]
        queryset_pagination = 1000

        # rebuild_from_value_list = True
        related_models = [Purchase, Transaction, TransactionPurchase]

    def get_instances_from_related(self, related_instance):
        """define how to retrieve the the related model if updated"""
        if isinstance(related_instance, Purchase):
            # refresh fetching related active transaction purchase
            if related_instance.transaction_purchase:
                purchase_transaction = TransactionPurchase.objects.filter(
                    status=Status.ACTIVE,
                    organization=related_instance.organization,
                    transaction__status=Status.ACTIVE,
                )
                return Purchase.objects.prefetch_related(
                    Prefetch('transaction_purchase', queryset=purchase_transaction)
                ).get(pk=related_instance.id)
            if related_instance.copied_from:
                return Purchase.objects.get(pk=related_instance.copied_from.id)
            # if related_instance.requisitions:
            #     return Purchase.objects.get(pk=related_instance.id).requisitions.all()
        # Update related purchase object after delete a transaction with a purchase
        if isinstance(related_instance, Transaction):
            if related_instance.status == Status.INACTIVE:
                purchase_transaction = TransactionPurchase.objects.filter(
                    status=Status.ACTIVE,
                    organization=related_instance.organization,
                    transaction__status=Status.ACTIVE
                )
                return related_instance.purchases.prefetch_related(
                    Prefetch('transaction_purchase', queryset=purchase_transaction)
                ).all()
        # Update related purchase object after create a transaction with a purchase
        if isinstance(related_instance, TransactionPurchase):
            if related_instance.status == Status.ACTIVE:
                purchase_transaction = TransactionPurchase.objects.filter(
                    status=Status.ACTIVE,
                    organization=related_instance.organization,
                    transaction__status=Status.ACTIVE
                )
                return Purchase.objects.prefetch_related(
                    Prefetch('transaction_purchase', queryset=purchase_transaction)
                ).get(pk=related_instance.purchase.id)

    def get_queryset(self, filters={}, orders=['-pk']):
        # filter to avoid order purchase item
        order_item_filters = {
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER
        }
        transaction_purchase = TransactionPurchase.objects.filter(
            status=Status.ACTIVE
        )
        queryset = Purchase.objects.prefetch_related(
            Prefetch('transaction_purchase', queryset=transaction_purchase)
        ).select_related(
            'organization',
            'person_organization_supplier',
            'person_organization_receiver',
            'department',
            'organization_department',
            'store_point',
        ).filter(
            **filters
        ).order_by(*orders)
        if filters:
            return queryset.filter(
                ~Q(status=Status.DISTRIBUTOR_ORDER)
            )
        return queryset.filter(
            ~Q(status__in=[Status.INACTIVE, Status.DISTRIBUTOR_ORDER])
        )


    # def get_list(self, filters={}):
    #     purchase_items = Purchase.objects.filter(
    #         status=Status.ACTIVE,
    #         purchase_type=PurchaseType.PURCHASE,
    #     )
    #     purchases = Purchase.objects.extra(
    #         select={'pk': 'id'}
    #     ).filter(
    #         ~Q(status=Status.INACTIVE)
    #     ).select_related(
    #         'organization',
    #         'person_organization_supplier',
    #         'person_organization_receiver',
    #         'department',
    #         'organization_department',
    #         'store_point',
    #     ).annotate(
    #         pending_amount=F('grand_total') - Coalesce(Sum(Case(
    #             When(
    #                 purchases__in=purchase_items,
    #                 then=F('purchases__grand_total')
    #             ),
    #             default=0.00
    #             )), 0.00)
    #     ).values(
    #         'id',
    #         'status',
    #         'alias',
    #         'organization',
    #         'organization__id',
    #         'is_sales_return',
    #         'purchase_date',
    #         'purchase_type',
    #         'purchase_payment',
    #         'purchase_order_status',
    #         'amount',
    #         'grand_total',
    #         'department',
    #             'department__id',
    #             'department__alias',
    #             'department__name',
    #             'department__description',
    #         'person_organization_supplier',
    #             'person_organization_supplier__id',
    #             'person_organization_supplier__alias',
    #             'person_organization_supplier__company_name',
    #             'person_organization_supplier__first_name',
    #             'person_organization_supplier__last_name',
    #             'person_organization_supplier__phone',
    #             'person_organization_supplier__person_group',
    #             'person_organization_supplier__email',
    #             'person_organization_supplier__opening_balance',
    #         'person_organization_receiver',
    #             'person_organization_receiver__id',
    #             'person_organization_receiver__alias',
    #             'person_organization_receiver__first_name',
    #             'person_organization_receiver__last_name',
    #             'person_organization_receiver__person_group',
    #             'person_organization_receiver__phone',
    #             'person_organization_receiver__code',
    #         'organization_department',
    #             'organization_department__id',
    #             'organization_department__alias',
    #             'organization_department__name',
    #         'copied_from',
    #             'copied_from__id',
    #             'copied_from__alias',
    #             'copied_from__vouchar_no',
    #         'store_point',
    #             'store_point__id',
    #             'store_point__alias',
    #             'store_point__name',
    #             'store_point__address',
    #             'store_point__phone',
    #             'store_point__type',
    #         'pending_amount',
    #     ).filter(**filters)

    #     purchase_with_transaction = list(purchases.filter(
    #         transaction_purchase__isnull=False,
    #         transaction_purchase__status=Status.ACTIVE,
    #         transaction_purchase__transaction__status=Status.ACTIVE,
    #     ))
    #     purchase_with_sales_return = list(purchases.filter(
    #         transaction_purchase__isnull=True,
    #         sales_return__isnull=False,
    #         sales_return__status=Status.ACTIVE
    #     ))
    #     # purchase_with_requisitions = list(purchases.filter(
    #     #     transaction_purchase__isnull=True,
    #     #     requisitions__isnull=False,
    #     #     requisitions__status=Status.DRAFT
    #     # ))
    #     without_transaction_and_sales_return = list(
    #         purchases.filter(
    #             transaction_purchase__isnull=True,
    #             sales_return__isnull=True,
    #         ))

    #     for item in purchase_with_transaction:
    #         purchase = Purchase.objects.get(id=item['id'])
    #         purchase_transaction_value_list = list(
    #             purchase.transaction_purchase.filter(
    #                 status=Status.ACTIVE,
    #                 transaction__status=Status.ACTIVE,
    #             ).values(
    #                 'id', 'transaction', 'transaction__organization_wise_serial', 'amount'
    #             )
    #         )
    #         transaction_purchase = []
    #         for value in purchase_transaction_value_list:
    #             transaction_purchase.append({
    #                 'id': value['id'],
    #                 'transaction': {
    #                     'id': value['transaction'],
    #                     'organization_wise_serial': \
    #                         value['transaction__organization_wise_serial']
    #                 },
    #                 'amount': value['amount']
    #             })
    #         item.update(
    #             {'transaction_purchase': transaction_purchase})

    #     for item in purchase_with_sales_return:
    #         purchase = Purchase.objects.get(id=item['id'])
    #         purchase_sales_return = list(purchase.sales_return.filter(
    #             status=Status.ACTIVE
    #         ).values('pk'))
    #         item.update({'sales_return': purchase_sales_return})

    #     # for item in purchase_with_requisitions:
    #     #     purchase = Purchase.objects.get(id=item['id'])
    #     #     purchase_requisitions = list(purchase.requisitions.filter(
    #     #         status=Status.DRAFT
    #     #     ).values('id', 'alias', 'vouchar_no'))
    #     #     item.update({'requisitions': purchase_requisitions})

    #     purchase_list = without_transaction_and_sales_return + \
    #         purchase_with_transaction + \
    #         purchase_with_sales_return
    #     return purchase_list



@registry.register_document
class ProductCategoryDocument(Document):
    name = fields.TextField(fields={'raw': fields.KeywordField()})
    status = fields.IntegerField()
    is_global = fields.IntegerField()
    organization = fields.ObjectField(properties={
        'pk': fields.IntegerField()
    })
    alias = fields.TextField()
    logo =  fields.ObjectField(
        properties={
            "full_size": fields.TextField(),
            "large": fields.TextField(),
            "small": fields.TextField(),
        }
    )

    def prepare_logo(self, instance):
        return prepare_image(
            instance.logo.name,
            "logo_images"
        )


    class Index:
        name = get_index('pharmacy_product_category')._name


    class Django:
        model = ProductCategory
        fields = [
            'id',
            'description'
        ]
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=['-pk']):
        return super(ProductCategoryDocument, self).get_queryset().select_related(
            'organization',
        ).filter(
            status=Status.ACTIVE
        ).filter(
            **filters
        ).order_by(*orders)


@registry.register_document
class StorePointDocument(Document):
    name = fields.TextField(fields={'raw': fields.KeywordField()})
    type = fields.IntegerField()
    status = fields.IntegerField()
    organization = fields.ObjectField(properties={
        'pk': fields.IntegerField()
    })
    alias = fields.TextField()
    auto_adjustment = fields.BooleanField()


    class Index:
        name = get_index('pharmacy_storepoint')._name


    class Django:
        model = StorePoint
        fields = [
            'id',
            'address',
            'phone'
        ]
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=['-pk']):
        return super(StorePointDocument, self).get_queryset().select_related(
            'organization'
        ).filter(
            status=Status.ACTIVE
        ).filter(
            **filters
        ).order_by(*orders)


@registry.register_document
class EmployeeStorePointDocument(Document):
    organization = fields.ObjectField(properties={
        'pk': fields.IntegerField()
    })
    employee = fields.ObjectField(properties={
        'pk': fields.IntegerField(),
        'code': fields.TextField(),
        'alias': fields.TextField(),
        'first_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'last_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'country': fields.TextField(),
        'designation': fields.ObjectField(properties={
            'pk': fields.IntegerField(),
            'alias': fields.TextField(),
            'name': fields.TextField(),
            'description': fields.TextField(),
            'department': fields.ObjectField(properties={
                'pk': fields.IntegerField(),
                'alias': fields.TextField(),
                'name': fields.TextField(),
                'description': fields.TextField(),
            })
        }),
        'degree': fields.TextField(),
        'dob': CustomDateField(),
        'gender': fields.IntegerField(),
        'phone': fields.TextField(),
    })
    store_point = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'name': fields.TextField(),
        'address': fields.TextField(),
        'phone': fields.TextField(),
        'type': fields.IntegerField()
    })
    alias = fields.TextField()


    class Index:
        name = get_index('pharmacy_employee_storepoint_access')._name


    class Django:
        model = EmployeeStorepointAccess
        fields = [
            'id',
            'access_status'
        ]
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=['-pk']):
        return super(EmployeeStorePointDocument, self).get_queryset().select_related(
            'organization',
            'employee',
            'employee__designation',
            'employee__designation__department',
            'store_point',
        ).filter(
            status=Status.ACTIVE
        ).filter(
            **filters
        ).order_by(*orders)


@registry.register_document
class StockDisbursementDocument(Document):
    status = fields.IntegerField()
    alias = fields.TextField()
    date = CustomDateField()
    organization = fields.ObjectField(properties={
        'pk': fields.IntegerField()
    })
    store_point = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'name': fields.TextField(),
        'address': fields.TextField(),
        'phone': fields.TextField(),
        'type': fields.IntegerField()
    })
    person_organization_employee = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'first_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'last_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'full_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'phone': fields.TextField(),
        'person_group': fields.IntegerField(),
        'degree': fields.TextField(),
        'designation': fields.ObjectField(properties={
            'id': fields.IntegerField(),
            'alias': fields.TextField(),
            'name': fields.TextField(),
            'description': fields.TextField(),
            'department': fields.ObjectField(properties={
                'id': fields.IntegerField(),
                'alias': fields.TextField(),
                'name': fields.TextField(),
                'description': fields.TextField(),
            })
        })
    })
    person_organization_patient = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'code': fields.TextField(),
        'first_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'last_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'full_name': fields.TextField(fields={'raw': fields.KeywordField()}),
        'dob': CustomDateField(),
        'phone': fields.TextField(),
        'person_group': fields.IntegerField(),
        # 'economic_status': fields.IntegerField(),

    })
    is_product_disbrustment = fields.BooleanField()
    patient_admission = fields.ObjectField(properties={
        'pk': fields.IntegerField()
    })
    service_consumed = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'subservice': fields.ObjectField(properties={
            'id': fields.IntegerField(),
            'alias': fields.TextField(),
            'name': fields.TextField()
        })
    })
    remarks = fields.TextField()
    adjustment_type = fields.IntegerField()


    class Index:
        name = get_index('pharmacy_stock_adjustment')._name


    class Django:
        model = StockAdjustment
        fields = [
            'id'
        ]
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=['-pk']):
        return super(StockDisbursementDocument, self).get_queryset().select_related(
            'store_point',
            'person_organization_patient',
            'person_organization_employee',
            'service_consumed',
            'service_consumed__subservice'
        ).filter(
            **filters
        ).filter(
            **es_filter()
        ).order_by(*orders)


@registry.register_document
class UnitDocument(Document):
    name = fields.TextField(fields={'raw': fields.KeywordField()})
    status = fields.IntegerField()
    is_global = fields.IntegerField()
    organization = fields.ObjectField(properties={
        'pk': fields.IntegerField()
    })
    alias = fields.TextField()


    class Index:
        name = get_index('pharmacy_unit')._name


    class Django:
        model = Unit
        fields = [
            'id',
            'description'
        ]
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=['-pk']):
        return super(UnitDocument, self).get_queryset().select_related(
            'organization',
        ).filter(
            status=Status.ACTIVE
        ).filter(
            **filters
        ).order_by(*orders)

    # def get_list(self):
    #     return ProductDisbursementCause.objects.values(
    #         'pk',
    #         'id',
    #         'name',
    #         'status',
    #         'alias',
    #         'organization',
    #             'organization__id',
    #         'is_global',
    #         'description'
    #     ).filter(status=Status.ACTIVE)

@registry.register_document
class StockDocument(Document):
    status = fields.IntegerField()
    is_out_of_stock = fields.BooleanField()
    delivery_date = CustomDateField()
    is_order_enabled = fields.BooleanField()
    orderable_stock = fields.FloatField()
    current_order_mode = fields.IntegerField()
    organization = fields.ObjectField(properties={
        "pk": fields.IntegerField()
    })
    store_point = fields.ObjectField(properties={
        "pk": fields.IntegerField()
    })
    ranking = fields.FloatField()
    product = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "alias": fields.TextField(),
            "order_mode": fields.IntegerField(),
            "is_published": fields.BooleanField(),
            "is_queueing_item": fields.BooleanField(),
            "is_salesable": fields.BooleanField(),
            "trading_price": fields.FloatField(),
            "discount_rate": fields.FloatField(),
            "product_discounted_price": fields.FloatField(),
            "order_limit_per_day": fields.IntegerField(),
            "order_limit_per_day_mirpur": fields.IntegerField(),
            "order_limit_per_day_uttara": fields.IntegerField(),
            "name": fields.TextField(
                analyzer=autocomplete_analyzer,
                fields={
                    "raw": fields.KeywordField(),
                    "suggest": fields.Completion(),
                }
            ),
            "image": fields.NestedField(
                properties={
                    "full_size": fields.TextField(),
                    "large": fields.TextField(),
                    "small": fields.TextField(),
                }
            ),
            "strength": fields.TextField(
                fields={
                    "raw": fields.KeywordField(),
                    "suggest": fields.Completion(),
                }
            ),
            "display_name": fields.TextField(
                analyzer=html_strip,
                fields={
                    "raw": fields.KeywordField(),
                    "suggest": fields.Completion(),
                }
            ),
            "full_name": fields.TextField(
                analyzer=html_strip,
                fields={
                    "raw": fields.KeywordField(),
                    "suggest": fields.Completion(),
                }
            ),
            "generic": fields.ObjectField(
                properties={
                    "alias": fields.TextField(),
                    "name": fields.TextField(
                        fields={
                            "raw": fields.KeywordField(),
                            "suggest": fields.Completion(),
                        }
                    ),
                }
            ),
            "manufacturing_company": fields.ObjectField(
                properties={
                    "id": fields.IntegerField(),
                    "alias": fields.KeywordField(),
                    "name": fields.TextField(
                        fields={
                            "raw": fields.KeywordField(),
                            "suggest": fields.Completion(),
                        }
                    ),
                }
            ),
            "form": fields.ObjectField(
                properties={
                    "alias": fields.TextField(),
                    "name": fields.TextField(
                        fields={
                            "raw": fields.KeywordField(),
                            "suggest": fields.Completion(),
                        }
                    ),
                }
            ),
            "subgroup": fields.ObjectField(
                properties={
                    "alias": fields.KeywordField(),
                    "product_group": fields.ObjectField(
                        properties={
                            "alias": fields.KeywordField(),
                        }
                    )
                }
            ),
        },
    )

    class Index:
        name = get_index("pharmacy_stock")._name
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "max_ngram_diff": 20
        }


    class Django:
        model = Stock
        fields = [
            "id",
            "alias",
        ]
        queryset_pagination = 1000
        ignore_signals = True

    def get_queryset(self, filters={}, orders=["-pk"], queryset=None):
        if isinstance(queryset, QuerySet):
            qs = queryset
        else:
            qs = super().get_queryset().select_related(
                "organization",
            ).filter(
                status=Status.ACTIVE,
            ).filter(
                **filters
            ).order_by(*orders)
        return qs.values(
            "id",
            "alias",
            "status",
            "orderable_stock",
            "organization_id",
            "store_point_id",
            "product_id",
            "product__alias",
            "product__name",
            "product__strength",
            "product__full_name",
            "product__display_name",
            "product__order_mode",
            "product__is_published",
            "product__is_queueing_item",
            "product__is_salesable",
            "product__trading_price",
            "product__discount_rate",
            "product__order_limit_per_day",
            "product__order_limit_per_day_mirpur",
            "product__order_limit_per_day_uttara",
            "product__image",
            "product__generic__alias",
            "product__generic__name",
            "product__form__alias",
            "product__form__name",
            "product__manufacturing_company__id",
            "product__manufacturing_company__alias",
            "product__manufacturing_company__name",
            "product__subgroup__alias",
            "product__subgroup__product_group__alias",
        )
    @classmethod
    def generate_id(cls, object_instance):
        """
        The default behavior is to use the Django object's pk (id) as the
        elasticseach index id (_id). If needed, this method can be overloaded
        to change this default behavior.
        """
        return object_instance["id"]

    def get_indexing_queryset(self,  filters={}):
        """
        Build queryset (iterator) for use by indexing.
        """
        qs = self.get_queryset().filter(**filters)
        kwargs = {}
        if self.django.queryset_pagination:
            kwargs = {'chunk_size': self.django.queryset_pagination}
        return qs.iterator(**kwargs)

    def prepare(self, instance):
        return prepare_stock_document(instance)

    def update(self, thing, refresh=None, action='index', parallel=False, **kwargs):
        """
        Update each document in ES for a model, iterable of models or queryset
        """
        if refresh is not None:
            kwargs['refresh'] = refresh
        elif self.django.auto_refresh:
            kwargs['refresh'] = self.django.auto_refresh

        if isinstance(thing, models.Model):
            object_list = self.get_queryset(filters={"pk": thing._get_pk_val()})
        else:
            object_list = thing

        return self._bulk(
            self._get_actions(object_list, action),
            parallel=parallel,
            **kwargs
        )


@registry.register_document
class PurchaseDocumentForOrder(Document):
    id = fields.TextField(
        fields={'raw': fields.KeywordField()}
    )
    status = fields.IntegerField()
    alias = fields.TextField()
    purchase_date = CustomDateField()
    amount = fields.DoubleField()
    grand_total = fields.DoubleField()
    discount_rate = fields.FloatField()
    round_discount = fields.FloatField()
    order_rating = fields.FloatField()
    order_rating_comment = fields.TextField()

    # Distributor order related fields
    distributor = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'primary_mobile': fields.TextField(),
        'address': fields.TextField()
    })
    distributor_order_group = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'sub_total': fields.FloatField(),
        'discount': fields.FloatField()
    })
    responsible_employee = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'first_name': fields.TextField(),
        'last_name': fields.TextField(),
        'phone': fields.TextField()
    })
    prev_order_date = CustomDateField(attr="prev_order_date")
    order_number_count = fields.IntegerField(attr="order_number_count")
    system_platform = fields.IntegerField()
    distributor_order_type = fields.IntegerField()
    current_order_status = fields.IntegerField()
    purchase_type = fields.IntegerField()
    organization = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(),
            'primary_mobile': fields.TextField(),
            'address': fields.TextField(),
            'delivery_sub_area': fields.TextField(),
            'delivery_thana': fields.IntegerField(),
            'active_issue_count': fields.IntegerField(),
            'entry_by': fields.ObjectField(
                properties={
                    'first_name': fields.TextField(),
                    'last_name': fields.TextField()
                }
            ),
        }
    )
    geo_location_data = fields.ObjectField(dynamic=True)
    is_queueing_order = fields.BooleanField()
    tentative_delivery_date = CustomDateField()
    calculated_profit = fields.FloatField()
    short_total = fields.FloatField(attr="short_total")
    return_total = fields.FloatField(attr="return_total")
    additional_discount = fields.FloatField()
    is_delayed = fields.BooleanField()


    def prepare_geo_location_data(self, instance):
        geo_data = instance.geo_location_data
        if not geo_data:
            return {}
        if isinstance(geo_data, str):
            json_acceptable_string = geo_data.replace("'", "\"")
            _data = json.loads(json_acceptable_string)
            return _data
        return dict(geo_data)


    class Index:
        name = get_index('pharmacy_purchase_orders')._name


    class Django:
        model = Purchase
        fields = [
            # 'id',
            'remarks',
            'vouchar_no'
        ]
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=['-pk']):
        queryset = Purchase.objects.select_related(
            "organization",
            "distributor",
            "responsible_employee",
            "distributor_order_group",
            "organization__entry_by",
        ).filter(
            status=Status.DISTRIBUTOR_ORDER,
            distributor_order_type=DistributorOrderType.ORDER,
            purchase_type=PurchaseType.VENDOR_ORDER,
            **filters
        ).order_by(*orders)
        if filters:
            return queryset.order_by(*orders)
        return queryset.filter(~Q(status=Status.INACTIVE))

    def get_indexing_queryset(self,  filters={}):
        """
        Build queryset (iterator) for use by indexing.
        """
        qs = self.get_queryset().filter(**filters)
        kwargs = {}
        if self.django.queryset_pagination:
            kwargs = {'chunk_size': self.django.queryset_pagination}
        return qs.iterator(**kwargs)
