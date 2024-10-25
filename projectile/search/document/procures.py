from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from procurement.models import Procure
from ..indexes import get_index


@registry.register_document
class ProcureDocument(Document):
    id = fields.IntegerField()
    alias = fields.TextField()
    date = fields.TextField()
    supplier = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "alias": fields.TextField(),
            "first_name": fields.TextField(),
            "last_name": fields.TextField(),
            "company_name": fields.TextField(),
            "phone": fields.TextField(),
            "code": fields.TextField(),
        }
    )
    contractor = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "alias": fields.KeywordField(),
            "first_name": fields.TextField(),
            "last_name": fields.TextField(),
            "phone": fields.TextField(),
        }
    )
    employee = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "alias": fields.KeywordField(),
            "first_name": fields.TextField(),
            "last_name": fields.TextField(),
            "phone": fields.TextField(),
            "code": fields.TextField(),
        }
    )
    requisition = fields.ObjectField(properties={"pk": fields.IntegerField()})
    sub_total = fields.TextField()
    discount = fields.TextField()
    operation_start = fields.TextField()
    operation_end = fields.TextField()
    remarks = fields.TextField()
    invoices = fields.TextField()
    estimated_collection_time = fields.TextField()
    current_status = fields.IntegerField()
    medium = fields.IntegerField()

    class Index:
        name = get_index("procurement_procure")._name

    class Django:
        model = Procure
        fields = []
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=["-pk"]):
        return (
            super()
            .get_queryset()
            .select_related(
                "supplier",
                "contractor",
                "employee",
            )
            .filter(**filters)
            .order_by(*orders)
        )
