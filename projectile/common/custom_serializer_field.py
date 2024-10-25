from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_str
from rest_framework import serializers
from rest_framework.relations import RelatedField
from elasticsearch_dsl import InnerDoc
from versatileimagefield.serializers import VersatileImageFieldSerializer


class UUIDRelatedField(RelatedField):
    """
    A read-write field that represents the target of the relationship
    by a unique 'uuid' attribute.
    """
    default_error_messages = {
        'does_not_exist': _('Object with {uuid_field}={value} does not exist.'),
        'invalid': _('Invalid value.'),
    }

    def __init__(self, model=None, fields=None, **kwargs):
        self.model = model

        self.fields = fields

        self.uuid_field = 'alias'

        super().__init__(**kwargs)

    def get_queryset(self):
        if self.model is None:
            self.model = self.parent.Meta.model

        if self.fields:
            return self.model.objects.filter().only(*self.fields)
        else:
            return self.model.objects.filter()

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(**{self.uuid_field: data})
        except ObjectDoesNotExist:
            self.fail('does_not_exist', uuid_name=self.uuid_field, value=smart_str(data))
        except (TypeError, ValueError):
            self.fail('invalid')

    def to_representation(self, obj):
        return obj


class CustomRelatedField(RelatedField):
    """
    A read-write field that represents the target of the relationship
    by a unique custom attribute.
    """
    default_error_messages = {
        'does_not_exist': _('Object with {look_up_field}={value} does not exist.'),
        'invalid': _('Invalid value.'),
    }

    def __init__(self, model=None, fields=None, look_up_field=None, **kwargs):
        if fields is None:
            fields = ["id"]
        if look_up_field is None:
            look_up_field = "pk"

        self.model = model

        self.fields = fields

        self.look_up_field = look_up_field

        super().__init__(**kwargs)

    def get_queryset(self):
        if self.model is None:
            self.model = self.parent.Meta.model

        if self.fields:
            return self.model.objects.filter().only(*self.fields)
        else:
            return self.model.objects.filter()

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(**{self.look_up_field: data})
        except ObjectDoesNotExist:
            self.fail('does_not_exist', look_up_field=self.look_up_field, value=smart_str(data))
        except (TypeError, ValueError):
            self.fail('invalid')

    def to_representation(self, obj):
        return obj


class ForeignKeyAliasField(serializers.Field):
    """
    Serializer field that returns the alias of a foreign key instead of its ID.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def bind(self, field_name, parent):
        super().bind(field_name, parent)

    def to_representation(self, value):
        related_object = value
        alias_value = getattr(related_object, 'alias')
        return alias_value


class CustomVersatileImageFieldSerializer(VersatileImageFieldSerializer):
    """
    Custom VersatileImageFieldSerializer adding elastic search support
    """

    def build_image_url(self, image_object):
        """_summary_

        Args:
            image_object (dict): versatile image object serialized

        Returns:
            _type_: image dict with proper image url
        """
        context_request = None
        if self.context:
            context_request = self.context.get('request', None)
        if image_object and context_request:
            for key, value in image_object.items():
                img_url = value
                image_object[key] = context_request.build_absolute_uri(img_url)
        return image_object

    def to_native(self, value):
        if isinstance(value, InnerDoc):
            return self.build_image_url(value.to_dict())
        return super().to_native(value)

