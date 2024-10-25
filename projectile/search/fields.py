from datetime import date
from dateutil import parser
from elasticsearch_dsl import Field
from elasticsearch_dsl.exceptions import ValidationException
from django_elasticsearch_dsl.fields import DEDField


class Date(Field):
    name = 'date'
    _coerce = True

    def _deserialize(self, data):
        if not data:
            return None
        if isinstance(data, date):
            return data

        try:
            # TODO: add format awareness
            return data
        except Exception as e:
            raise ValidationException('Could not parse date from the value (%r)' % data, e)


class CustomDateField(DEDField, Date):
    pass


class Time(Field):
    name = 'time'
    _coerce = True

    def _deserialize(self, data):
        if not data:
            return None
        if isinstance(data, date):
            return data

        try:
            # TODO: add format awareness
            return parser.parse(data).time()
        except Exception as e:
            raise ValidationException('Could not parse time from the value (%r)' % data, e)


class CustomTimeField(DEDField, Time):
    pass
