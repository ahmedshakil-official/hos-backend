from urllib import request
from rest_framework.serializers import ModelSerializer
from .models import NameSlugDescriptionBaseModel

from pharmacy.models import DamageProduct, RecheckProduct

class NameSlugDescriptionBaseModelSerializer(ModelSerializer):
    class Meta:
        model = NameSlugDescriptionBaseModel
        fields = (
            'name',
            'slug',
            'description'
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
        )


class DynamicFieldsModelSerializer(ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request', None)
        if request:
            _fields = request.query_params.get('fields', '')
            if _fields:
                fields = _fields.split(',')

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)
