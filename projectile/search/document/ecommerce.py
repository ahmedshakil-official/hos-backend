from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django.db.models.query import QuerySet
from django.db.models import Prefetch
from django.db import models
from common.enums import Status
from common.helpers import prepare_es_populate_filter as es_filter

from ecommerce.models import OrderInvoiceGroup

from ..indexes import get_index
from ..fields import CustomDateField


@registry.register_document
class OrderInvoiceGroupDocument(Document):
    id = fields.TextField(
        fields={'raw': fields.KeywordField()}
    )
    current_order_status = fields.IntegerField()
    alias = fields.TextField()
    status = fields.IntegerField()
    date = CustomDateField()
    delivery_date = CustomDateField()
    sub_total = fields.DoubleField()
    discount = fields.DoubleField()
    round_discount = fields.DoubleField()
    additional_cost = fields.DoubleField()
    additional_discount = fields.DoubleField()
    total_short = fields.DoubleField()
    total_return = fields.DoubleField()
    # additional_cost = fields.DoubleField()
    # additional_cost = fields.DoubleField()
    order_by_organization = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'alias': fields.TextField(),
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
    organization = fields.ObjectField(properties={
        'pk': fields.IntegerField()
    })
    responsible_employee = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'alias': fields.TextField(),
        'first_name': fields.TextField(),
        'last_name': fields.TextField(),
        'phone': fields.TextField(),
        'code': fields.TextField(),
    })
    orders = fields.ObjectField(properties={
        'pk': fields.TextField(
            fields={'raw': fields.KeywordField()}
        )
    })
    related_invoice_groups = fields.NestedField(
        properties={
            'id': fields.IntegerField(),
            'current_order_status': fields.IntegerField(),
            'responsible_employee': fields.ObjectField(
                properties={
                    'id': fields.IntegerField(),
                    'alias': fields.TextField(),
                    'first_name': fields.TextField(),
                    'last_name': fields.TextField(),
                    'phone': fields.TextField(),
                    'code': fields.TextField(),
                }
            ),
        },
        attr="related_invoice_groups"
    )
    customer_rating = fields.IntegerField()

    class Index:
        name = get_index('ecommerce_order_invoice_group')._name


    class Django:
        model = OrderInvoiceGroup
        fields = []
        queryset_pagination = 1000
        # rebuild_from_value_list = True

    def get_queryset(self, filters={}, orders=['-pk'], _queryset=None):
        if isinstance(_queryset, QuerySet):
            queryset = _queryset
        else:
            queryset = super().get_queryset()
        queryset = queryset.select_related(
            'order_by_organization',
            'order_by_organization__entry_by',
            'responsible_employee',
            'organization',
        ).prefetch_related(
            Prefetch(
                "orders",
            ),
        ).filter(
            status=Status.ACTIVE,
        ).filter(
            **filters
        ).order_by(*orders)
        return queryset

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
