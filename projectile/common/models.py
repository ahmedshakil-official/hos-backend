from __future__ import unicode_literals

import os
import uuid
import logging
import pprint
import datetime
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from autoslug import AutoSlugField
from enumerify import fields
from common.utils import (
    create_cache_key_name,
    get_organization_wise_serial,
    mime_content_type,
)
from pharmacy.enums import SalesInactiveType
from .enums import PublishStatus, Status
from .validators import admin_validate_unique_name_with_org

logger = logging.getLogger(__name__)
USER_IP_ADDRESS = ''

# set uploaded files folder location
def get_upload_to(instance, filename):
    return 'contents/%s/%s' % (str(instance.__class__.__name__).lower(), filename)

class CreatedAtUpdatedAtBaseModel(models.Model):
    alias = models.UUIDField(
        default=uuid.uuid4, editable=False, db_index=True, unique=True)
    status = fields.SelectIntegerField(blueprint=Status, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    entry_by = models.ForeignKey(
        'core.Person',
        models.DO_NOTHING,
        default=None,
        null=True,
        verbose_name=('entry by'),
        related_name="%(app_label)s_%(class)s_entry_by"
    )

    updated_by = models.ForeignKey(
        'core.Person',
        models.DO_NOTHING,
        default=None,
        null=True,
        verbose_name=('last updated by'),
        related_name="%(app_label)s_%(class)s_updated_by"
    )
    organization_wise_serial = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text='OrganizationWise Serial Number'
    )
    user_ip = models.GenericIPAddressField(null=True, blank=True, editable=False,)
    class Meta:
        abstract = True
        ordering = ('-created_at',)

    def _print(self):
        _pp = pprint.PrettyPrinter(indent=4)
        _pp.pprint("------------------------------------------")
        logger.info("Details of {} : ".format(self))
        _pp.pprint(vars(self))
        _pp.pprint("------------------------------------------")

    def to_dict(self, _fields=None, _exclude=None):
        from django.forms.models import model_to_dict
        return model_to_dict(self, _fields, _exclude)

    @staticmethod
    def queryset_to_list(qs, fields=None, exclude=None, fk_fields=None):
        fk_fields = fk_fields or []
        data_list=[]
        for item in qs:
            dict_item = item.to_dict(_fields=fields, _exclude=exclude)
            for field in fk_fields:
                dict_item['{}_id'.format(field)] = dict_item.pop(field)
            data_list.append(
                dict_item
            )
        return data_list

    def get_specific_attribute(self, attribute, date=None, object_filter={}, primary_params="created_at"):
        """
        Create a queryset which is filtered with date and some additional filter.
        queryset contains less than 3 attributes/fields for each model object.

        :param attribute: string (model field/column name) [required]
        :param date: string [default value is today]
        :param object_filter: dictionary
        :param primary_params: string
        :return: queryset object
        """
        if date is None:
            date = timezone.make_aware(
                datetime.datetime.today(),
                timezone.get_current_timezone()
            )
        elif isinstance(date, str):
            date = timezone.make_aware(
                datetime.datetime.strptime(date, "%Y-%m-%d"),
                timezone.get_current_timezone()
            )

        required_field = []

        if hasattr(self.__class__, primary_params):
            required_field.append(primary_params)
            object_filter.update({
                primary_params + "__date": date
            })

        if hasattr(self.__class__, attribute):
            required_field.append(attribute)

        return self.__class__.objects.filter(**object_filter).values(*required_field)

    def get_all_actives(self):
        return self.__class__.objects.filter(
            status=Status.ACTIVE
        ).order_by('-pk')

    def get_all(self):
        return self.__class__.objects.filter()

    def get_all_non_inactives(self):
        return self.__class__.objects.exclude(
            status=Status.INACTIVE
        ).order_by('-pk')

    def get_instance_by_property(self, filters=None):
        """[summary]

        Args:
            filters ([filter object], optional): [description]. Defaults to None.

        Returns:
            [object]: [a single model object]
        """
        if filters:
            try:
                return self.__class__.objects.get(
                    status=Status.ACTIVE,
                    **filters
                )
            except (self.__class__.DoesNotExist, self.__class__.MultipleObjectsReturned):
                return None
        return None

    def field_exists(self, field):
        try:
            self.__class__._meta.get_field(field)
            return True
        except models.FieldDoesNotExist:
            return False

    def save(self, *args, **kwargs):

        # from core.models import (
        #     Person,
        #     PersonOrganization,
        #     PersonOrganizationGroupPermission
        # )
        # from pharmacy.models import (
        #     Purchase,
        #     StockIOLog,
        #     DistributorOrderGroup,
        #     OrderTracking
        # )

        # key = self.get_serial_key()
        # cache_serial_flag = False
        # cache_serial_models = (
        #     # Sales,
        #     Purchase,
        #     StockIOLog,
        #     # Transaction,
        #     # ServiceConsumedGroup,
        #     # ServiceConsumed,
        #     # AppointmentTreatmentSession,
        #     # AppointmentServiceConsumed,
        #     Person,
        #     PersonOrganization,
        #     # PersonOrganizationSalary,
        #     PersonOrganizationGroupPermission,
        # )

        # if isinstance(self, cache_serial_models):
        #     cache_serial_flag = True

        # if self._state.adding:
        #     self.organization_wise_serial = self.get_last_serial(cache_serial_flag)
        #     if cache_serial_flag:
        #         cache.set(key, self.organization_wise_serial + 1, 60*60*24)
        # else:
        #     _status = self.__class__.objects.values_list('status', flat=True).get(pk=self.pk)
        #     if (_status or self.status) is not Status.INACTIVE and \
        #     _status is not self.status and self.status is Status.ACTIVE:
        #         self.organization_wise_serial = self.get_last_serial(cache_serial_flag)
        #         cache.set(key, self.organization_wise_serial + 1, 60*60*24)

        self.user_ip = USER_IP_ADDRESS

        super().save(*args, **kwargs)

    def get_serial_key(self):
        model_str = (type(self).__name__)
        organization_id = 0
        if hasattr(self, 'organization_id') and self.organization_id:
            organization_id = self.organization_id
        return "serial_{}_{}_{}_last_count".format(organization_id, self.status, model_str)

    def get_last_serial(self, cache_serial_flag=False):
        from pharmacy.models import OrderTracking

        if isinstance(self, OrderTracking):
            return 1
        if cache_serial_flag:
            last_serial = cache.get(self.get_serial_key(), None)
            if last_serial is not None:
                return last_serial
        return self.get_organization_wise_serial()

    def get_organization_wise_serial(self):
        from core.models import PersonOrganization, Person
        from pharmacy.models import Sales

        # dealing query if cache not found
        if hasattr(self, 'organization'):
            serial_data = self.__class__.objects.filter(
                organization=self.organization,
                status__in=[self.status, Status.INACTIVE]
            ).only('id')
            if isinstance(self, (Person, PersonOrganization)):
                serial_data = serial_data.filter(
                    person_group=self.person_group,
                )
        else:
            serial_data = self.__class__.objects.filter(
                status__in=[self.status, Status.INACTIVE]
            ).only('id')

        #calculating serial

        # categorize sales serial for different types of sales
        if isinstance(self, Sales):
            exclude_types = [SalesInactiveType.FROM_EDIT]
            if self.status == Status.ACTIVE:
                exclude_types.append(SalesInactiveType.FROM_ON_HOLD)
                serial_data = serial_data.exclude(
                    inactive_from__in=exclude_types
                )
            elif self.status == Status.ON_HOLD:
                exclude_types.append(SalesInactiveType.FROM_ACTIVE)
                serial_data = serial_data.exclude(
                    inactive_from__in=exclude_types
                )

        return serial_data.count() + 1

class CreatedAtUpdatedAtBaseModelWithOrganization(CreatedAtUpdatedAtBaseModel):
    organization = models.ForeignKey(
        'core.Organization',
        models.DO_NOTHING,
        blank=False,
        null=False,
        db_index=True,
        verbose_name=('organization name')
    )

    class Meta:
        abstract = True
        index_together = ["organization", "status"]
        ordering = ('-created_at',)

    def get_active_from_organization(
            self,
            organization_instance,
            order_by='pk',
            related_fields=None,
            only_fields=None
    ):
        if related_fields is None:
            related_fields = []
        if only_fields is None:
            only_fields = []
        if order_by is None:
            return self.__class__.objects.filter(
                organization=organization_instance,
                status=Status.ACTIVE
            ).select_related(*related_fields).only(*only_fields)
        else:
            return self.__class__.objects.filter(
                organization=organization_instance,
                status=Status.ACTIVE
            ).select_related(*related_fields).only(
                *only_fields
            ).order_by(order_by)

    def get_all_from_organization(
            self,
            organization_instance,
            filter_status=None,
            order_by=None,
            related_fields=None,
            only_fields=None
            ):
        if related_fields is None:
            related_fields = []
        if only_fields is None:
            only_fields = []
        if filter_status is None:
            if order_by is None:
                return self.__class__.objects.filter(
                    Q(organization=organization_instance)
                ).select_related(*related_fields).only(*only_fields)
            else:
                return self.__class__.objects.filter(
                    Q(organization=organization_instance)
                ).select_related(*related_fields).only(
                    *only_fields
                ).order_by(order_by)
        else:
            if order_by is None:
                return self.__class__.objects.filter(
                    Q(organization=organization_instance)
                ).select_related(*related_fields).only(
                    *only_fields
                ).filter(status=filter_status)
            else:
                return self.__class__.objects.filter(
                    Q(organization=organization_instance)
                ).select_related(*related_fields).only(
                    *only_fields
                ).filter(status=filter_status).order_by(order_by)


class NameSlugDescriptionBaseModel(CreatedAtUpdatedAtBaseModel):
    name = models.CharField(max_length=200, db_index=True)
    slug = AutoSlugField(populate_from='name', always_update=True, unique=True, allow_unicode=True)
    description = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, Name: {}, Slug: {}".format(self.id, self.name, self.slug)


class NameSlugDescriptionCodeBaseModel(NameSlugDescriptionBaseModel):
    code = models.CharField(max_length=32)

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, Name: {}, Slug: {}".format(self.id, self.name, self.code)


class NameSlugDescriptionBaseOrganizationWiseModel(NameSlugDescriptionBaseModel):
    organization = models.ForeignKey(
        'core.Organization',
        models.DO_NOTHING,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=('organization name')
    )
    clone = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    is_global = fields.SelectIntegerField(
        blueprint=PublishStatus, default=PublishStatus.PRIVATE)
    objects = models.Manager()

    class Meta:
        abstract = True

    def get_name(self):
        try:
            return u"ID: {}, Name: {}, Slug: {}".format(self.clone.id,
                                                        self.clone.name,
                                                        self.clone.slug)
        except AttributeError:
            return u"ID: {}, Name: {}, Slug: {}".format(self.id, self.name, self.slug)

    def get_is_global(self):
        if self.is_global != PublishStatus.PRIVATE:
            return True
        return False

    def get_belong_to_organization(self, organization_id):
        if self.organization__id == organization_id:
            return True
        return False

    def get_is_accessible_by_organization(self, organization_id):
        if self.is_global != PublishStatus.PRIVATE:
            return True
        if self.organization__id == organization_id:
            return True
        return False

    def get_all_from_organization(
            self,
            organization_instance,
            filter_status=None,
            order_by=None,
            related_fields=None,
            only_fields=None
    ):
        if related_fields is None:
            related_fields = []
        if only_fields is None:
            only_fields = []
        if filter_status is None:
            if order_by is None:
                return self.__class__.objects.filter(
                    Q(organization=organization_instance) |
                    ~Q(is_global=PublishStatus.PRIVATE)
                ).select_related(*related_fields).only(*only_fields)
            else:
                return self.__class__.objects.filter(
                    Q(organization=organization_instance) |
                    ~Q(is_global=PublishStatus.PRIVATE)
                ).select_related(
                    *related_fields
                ).only(*only_fields).order_by(order_by)
        else:
            if order_by is None:
                return self.__class__.objects.filter(
                    Q(organization=organization_instance) |
                    ~Q(is_global=PublishStatus.PRIVATE)
                ).select_related(*related_fields).only(*only_fields)
            else:
                return self.__class__.objects.filter(
                    Q(organization=organization_instance) |
                    ~Q(is_global=PublishStatus.PRIVATE)
                ).select_related(*related_fields).only(
                    *only_fields
                ).filter(status=filter_status).order_by(order_by)

    def clean(self):
        admin_validate_unique_name_with_org(self)


class OrganizationWiseCreatedAtUpdatedAtBaseModelWithGlobal(CreatedAtUpdatedAtBaseModel):
    organization = models.ForeignKey(
        'core.Organization',
        models.DO_NOTHING,
        blank=True,
        null=True,
        db_index=True,
        default=None,
        verbose_name=('organization name')
    )
    clone = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True, default=None)
    is_global = fields.SelectIntegerField(
        blueprint=PublishStatus, default=PublishStatus.PRIVATE)

    class Meta:
        abstract = True

    def get_is_global(self):
        if self.is_global != PublishStatus.PRIVATE:
            return True
        return False

    def get_belong_to_organization(self, organization_id):
        if self.organization__id == organization_id:
            return True
        return False

    def get_is_accessible_by_organization(self, organization_id):
        if self.is_global != PublishStatus.PRIVATE:
            return True
        if self.organization__id == organization_id:
            return True
        return False

    def get_all_from_organization(
            self,
            organization_instance,
            filter_status=None,
            order_by=None,
            related_fields=None,
            only_fields=None
        ):
        if related_fields is None:
            related_fields = []
        if only_fields is None:
            only_fields = []
        if filter_status is None:
            if order_by is None:
                return self.__class__.objects.filter(
                    Q(organization=organization_instance) |
                    ~Q(is_global=PublishStatus.PRIVATE)
                ).select_related(*related_fields).only(*only_fields)
            else:
                return self.__class__.objects.filter(
                    Q(organization=organization_instance) |
                    ~Q(is_global=PublishStatus.PRIVATE)
                ).select_related(
                    *related_fields
                ).only(*only_fields).order_by(order_by)
        else:
            if order_by is None:
                return self.__class__.objects.filter(
                    Q(organization=organization_instance) |
                    ~Q(is_global=PublishStatus.PRIVATE)
                ).select_related(*related_fields).only(*only_fields)
            else:
                return self.__class__.objects.filter(
                    Q(organization=organization_instance) |
                    ~Q(is_global=PublishStatus.PRIVATE)
                ).select_related(*related_fields).only(
                    *only_fields
                ).filter(status=filter_status).order_by(order_by)


class FileStorage(CreatedAtUpdatedAtBaseModel):
    content = models.FileField(upload_to=get_upload_to, null=True, blank=True)
    name = models.CharField(max_length=1024, null=True, blank=True, editable=False)
    content_type = models.CharField(max_length=64, null=True, blank=True, editable=False)
    description = models.TextField(null=True, blank=True)

    # pylint: disable=old-style-class, no-init
    class Meta:
        abstract = True

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, Name: {}, Type: {}".format(self.id, self.name, self.content_type)


    def save(self, *args, **kwargs):
        if self.content:
            dir_, self.name = os.path.split(self.content.name)
            self.content_type = mime_content_type(self.content.name)
        super(FileStorage, self).save(*args, **kwargs)
