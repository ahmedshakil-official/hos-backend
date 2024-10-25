from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from core.models import Area
from ..indexes import get_index


@registry.register_document
class AreaDocument(Document):
    id = fields.IntegerField(attr="id")
    slug = fields.TextField(attr="slug")
    alias = fields.KeywordField(attr="alias")
    code = fields.KeywordField(attr="code")
    status = fields.IntegerField(attr="status")

    class Index:
        name = get_index("core_area")._name

    class Django:
        model = Area
        fields = [
            "name",
            "discount_factor",
            "description",
        ]
        queryset_pagination = 1000

    def get_queryset(self, filters={}, orders=["-pk"]):
        return super().get_queryset().filter(**filters).order_by(*orders)
