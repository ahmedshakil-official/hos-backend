# for python3 compatibility
import datetime

from django.utils import timezone
from future.builtins import round

import logging
import pandas as pd
import os

from django.core.cache import cache
from django.db import transaction, IntegrityError

from sorl.thumbnail import delete

from common.enums import Status
from common.cache_helpers import delete_qs_count_cache
from common.cache_keys import DELIVERY_AREA_HUB_ID_CACHE_KEY, ORGANIZATION_AND_AREA_DISCOUNT_CACHE_KEY
from common.helpers import populate_es_index
from common.cache_helpers import get_or_clear_cumulative_discount_factor, clear_organization_and_area_discount_cache
from core.choices import ResetStatus

from core.enums import (
    PersonGroupType,
    OrganizationType,
    IssueTrackingStatus,
    FilePurposes,
)
from core.utils import (
    get_person_and_person_organization_common_arguments,
    create_person_organization,
    create_person_organization_instance,
    user_detail_cache_expires_by_organization_delivery_thana
)


logger = logging.getLogger(__name__)


def send_activation_mail(sender, created, **kwargs):
    pass


def change_status_of_organization_related_instances(previous_status, change_to_be, model):
    items = model.filter(status=previous_status)
    for item in items:
        item.status = change_to_be
        item.save()


def post_save_person(sender, instance, created, **kwargs):
    if created:
        # add person
        if instance.person_group is not PersonGroupType.OTHER:
            # create a person organization with the same attribute values
            create_person_organization_instance(
                instance
            )

@transaction.atomic()
def post_save_employee(sender, instance, created, **kwargs):

    # Expire user profile details cache
    instance.delete_user_profile_details_cache()



# pylint: disable=unused-argument
@transaction.atomic
def pre_save_person_organization(sender, instance, **kwargs):
    """
    perform some trigger operation
    """

    instance.person.delete_user_profile_details_cache()
    # Expire tagged supplier and contractor cache
    instance.expire_tagged_supplier_cache()
    instance.rebuild_tagged_contractor_cache()
    logger.info("Rebuild tagged contractor cache")

    populate_es_index(
        'core.models.PersonOrganization',
        {'id__in': [instance.id]},
    )

    delete_qs_count_cache(sender)


def pre_save_organization_settings(sender, instance, **kwargs):

    from pharmacy.models import StorePoint, Stock
    from common.tasks import cache_expire_list
    from pharmacy.tasks import update_product_queueing_item_value
    organization = instance.organization
    is_distributor = organization.type == OrganizationType.DISTRIBUTOR

    if not instance._state.adding:
        # Expire organization setting cache
        organization.expire_cache(False)

    # Expire stocks cache if price type has changed
    settings = organization.get_settings_instance()
    if not instance._state.adding and is_distributor:

        # Get all storepoints of an organization
        storepoints = StorePoint.objects.filter(
            organization=organization,
            status=Status.ACTIVE
        ).values_list('id', flat=True)

        # Get Store Point Wise stocks
        for storepoint in storepoints:
            # Only update stock with product is_salesable True
            stocks = Stock.objects.filter(
                organization__id=instance.organization_id,
                status=Status.ACTIVE,
                product__is_salesable=True,
                store_point__id=storepoint
            ).values_list('id', flat=True)

            base_key = "stock_instance"

            cache_key_list = ["{}_{}".format(base_key, str(item).zfill(12)) for item in stocks]
            if is_distributor:
                # distributor_cache_key_list = ["{}_{}".format("stock_instance_distributor", str(item).zfill(12)) for item in stocks]
                # if instance.allow_order_from == AllowOrderFrom.OPEN and not instance.overwrite_order_mode_by_product:
                #     products = Product.objects.filter(
                #         organization__id=instance.organization_id,
                #         status=Status.ACTIVE,
                #         is_queueing_item=True
                #     )
                #     products.update(is_queueing_item=False)
                # elif instance.overwrite_order_mode_by_product:
                #     products = Product.objects.filter(
                #         organization__id=instance.organization_id,
                #         status=Status.ACTIVE,
                #         order_mode=AllowOrderFrom.OPEN
                #     )
                #     products.update(is_queueing_item=False)

                # Fix queueing_item value
                _chunk_size = 400
                _number_of_operation = int((stocks.count() / _chunk_size) + 1)

                _lower_limit = 0
                _upper_limit = _chunk_size
                for _ in range(0, _number_of_operation):
                    stock_pks = list(stocks[_lower_limit:_upper_limit])
                    # update_product_queueing_item_value.delay(
                    #     stock_pks,
                    #     instance.to_dict(
                    #         _fields=['overwrite_order_mode_by_product', 'allow_order_from']
                    #     )
                    # )
                    update_product_queueing_item_value.apply_async(
                        (
                            stock_pks,
                            instance.to_dict(
                                _fields=['overwrite_order_mode_by_product', 'allow_order_from']
                            ),
                        ),
                        countdown=10,
                        retry=True, retry_policy={
                            'max_retries': 10,
                            'interval_start': 0,
                            'interval_step': 0.2,
                            'interval_max': 0.2,
                        }
                    )
                    # cache_expire_list.apply_async(
                    #     ((distributor_cache_key_list[_lower_limit:_upper_limit]),),
                    #     countdown=60,
                    #     retry=True,
                    #     retry_policy={
                    #         'max_retries': 10,
                    #         'interval_start': 0,
                    #         'interval_step': 0.2,
                    #         'interval_max': 0.2,
                    #     }
                    # )
                    _lower_limit = _upper_limit
                    _upper_limit = _lower_limit + _chunk_size

            number_of_key = stocks.count()
            index = 0
            chunk_size = 5000

            while index < number_of_key:

                cache_expire_list.apply_async(
                    ((cache_key_list[index:index+chunk_size]),),
                    countdown=60,
                    retry=True,
                    retry_policy={
                        'max_retries': 10,
                        'interval_start': 0,
                        'interval_step': 0.2,
                        'interval_max': 0.2,
                    }
                )
                # if is_distributor:
                #     cache_expire_list.apply_async(
                #         ((distributor_cache_key_list[index:index+chunk_size]),),
                #         countdown=60,
                #         retry=True,
                #         retry_policy={
                #             'max_retries': 10,
                #             'interval_start': 0,
                #             'interval_step': 0.2,
                #             'interval_max': 0.2,
                #         }
                #     )

                index = index + chunk_size + 1

@transaction.atomic
def pre_save_organization(sender, instance, **kwargs):
    if not instance._state.adding:
        # Expire related cache keys
        instance.expire_cache(celery=False)
        pre_organization = sender.objects.get(id=instance.id)
        if pre_organization.status == Status.ACTIVE \
            and instance.status == Status.SUSPEND:
            change_status_of_organization_related_instances(
                Status.ACTIVE, Status.SUSPEND, instance.accounts_set
            )
            change_status_of_organization_related_instances(
                Status.ACTIVE, Status.SUSPEND, instance.storepoint_set
            )
        if pre_organization.status == Status.SUSPEND \
            and instance.status == Status.ACTIVE:
            change_status_of_organization_related_instances(
                Status.SUSPEND, Status.ACTIVE, instance.accounts_set
            )
            change_status_of_organization_related_instances(
                Status.SUSPEND, Status.ACTIVE, instance.storepoint_set
            )

def pre_save_group_permission(sender, instance, **kwargs):
    if not instance._state.adding:
        permission_pattern = "permission_{}*".format(
            str(instance.person_organization.id).zfill(7)
        )
        cache.delete_pattern(permission_pattern, itersize=10000)


@transaction.atomic
def post_save_organization(sender, instance, created, **kwargs):
    from core.models import OrganizationSetting, Person, Area
    from common.healthos_helpers import HealthOSHelper
    if created:
        persons = Person.objects.filter(
            status=Status.ACTIVE,
            person_group__in=(PersonGroupType.SYSTEM_ADMIN,  PersonGroupType.MONITOR,)
        )
        for item in persons:
            arguments = {}
            arguments = get_person_and_person_organization_common_arguments(
                item
            )
            arguments['organization'] = instance
            create_person_organization(**arguments)

        OrganizationSetting.objects.get_or_create(
            organization=instance,
            status=Status.ACTIVE
        )
        # get the delivery thana/ area for the organization
        area = instance.delivery_thana
        if area:
            # Create an instance of healthos helper
            healthos_helper = HealthOSHelper()
            # Get the delivery area to delivery hub id mappings dictionary
            delivery_area_hub_ids = healthos_helper.get_delivery_area_hub_id_list()
            delivery_hub_id = delivery_area_hub_ids.get(str(area), None)
            # add area fk for the selected thana code
            try:
                area_fk = Area().get_all_actives().get(code=instance.delivery_thana)
                instance.area = area_fk
            except Area.DoesNotExist:
                logger.info(f"Area no found for given thana {area}")
            # Add the delivery hub for the organization
            instance.delivery_hub_id = delivery_hub_id
            instance.save()

    populate_es_index(
        'core.models.Organization',
        {'id__in': [instance.id]},
    )
    # Delete qs count cache
    delete_qs_count_cache(sender)

    # Delete organization and area discount factors
    cache_key = ORGANIZATION_AND_AREA_DISCOUNT_CACHE_KEY + str(instance.id)
    cache.delete(cache_key)

    cache_key = f"cart_group_{instance.id}"
    organization_data = cache.get(cache_key) or {}
    if created or 'min_order_amount' not in organization_data or organization_data[
        'min_order_amount'] != instance.min_order_amount:
        organization_data['min_order_amount'] = instance.min_order_amount
        cache.set(cache_key, organization_data)

def delete_images(sender, instance, **kwargs):
    """
    deletes the images from the directory
    """
    # logger.debug('Deleting image with data {} {} {}'.format(sender, instance, kwargs))
    if instance.profile_image:
        # Delete the thumbnail image
        delete(instance.profile_image)
        # Delete the image file from filesystem
        instance.profile_image.delete(False)

    if instance.hero_image:
        # Delete the thumbnail image
        delete(instance.hero_image)
        # Delete the image file from filesystem
        instance.hero_image.delete(False)


@transaction.atomic
def post_save_issue_status(sender, instance, created, **kwargs):
    from common.tasks import cache_expire_list
    from common.helpers import custom_elastic_rebuild
    from pharmacy.models import Purchase
    from pharmacy.enums import DistributorOrderType, PurchaseType
    from .models import Issue

    _instance = instance
    _issue = _instance.issue
    if created:
        if _issue.current_issue_status != _instance.issue_status:
            _issue.current_issue_status = _instance.issue_status
        _issue.save(update_fields=['current_issue_status',])
        # Update active issue count of organization
        active_issue_count = Issue.objects.filter(
            status=Status.ACTIVE,
            issue_organization__id=_issue.issue_organization_id,
        ).exclude(
            current_issue_status__in=[IssueTrackingStatus.RESOLVED, IssueTrackingStatus.REJECTED]
        ).only('id').count()
        _issue.issue_organization.active_issue_count = active_issue_count
        _issue.issue_organization.save(update_fields=['active_issue_count'])

        filters = {
            "status": Status.DISTRIBUTOR_ORDER,
            "distributor_order_type": DistributorOrderType.ORDER,
            "purchase_type": PurchaseType.VENDOR_ORDER,
            "organization": _issue.issue_organization_id
        }
        order_key_list = []

        orders = list(Purchase.objects.values_list(
            'pk', flat=True
        ).filter(**filters).order_by('-pk'))

        for order_id in orders:
            order_key_list.append('purchase_distributor_order_{}'.format(str(order_id).zfill(12)))

        cache_expire_list.apply_async(
            (order_key_list, ),
            countdown=5,
            retry=True, retry_policy={
                'max_retries': 10,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
        custom_elastic_rebuild(
            'pharmacy.models.Purchase', {'pk__in': orders})


@transaction.atomic
def post_save_script_file_storage(sender, instance, created, **kwargs):
    from pharmacy.tasks import set_ecom_stock_from_file_lazy

    from procurement.tasks import create_purchase_prediction_from_file_lazy

    if instance.date is None:
        instance.date = datetime.date.today()
        instance.save(update_fields=['date'])

    if created and instance.set_stock_from_file and instance.file_purpose == FilePurposes.DISTRIBUTOR_STOCK:
        chunk_size = 500
        stock_df =  pd.read_csv(instance.content)
        row, column = stock_df.shape
        index = 0
        while index < row:
            next_index = index + chunk_size
            # adjust_stock_from_file_ecommerce.delay(
            #     instance.name,
            #     instance.pk,
            #     index,
            #     next_index,
            #     store_point_id
            # )
            set_ecom_stock_from_file_lazy.apply_async(
                (
                    instance.name,
                    instance.pk,
                    index,
                    next_index,
                ),
                countdown=5,
                retry=True, retry_policy={
                    'max_retries': 10,
                    'interval_start': 0,
                    'interval_step': 0.2,
                    'interval_max': 0.2,
                }
            )
            index = next_index
    elif created and instance.file_purpose == FilePurposes.PURCHASE_PREDICTION:
        purchase_prediction_columns = [
            'ID',
            'MRP',
            'SP',
            'AVG',
            'L_RATE',
            'H_RATE',
            'KIND',
            'STATUS',
            'OSTOCK',
            'SELL',
            'PUR',
            'SHORT',
            'RET',
            'NSTOCK',
            'PRED',
            'NORDER',
            'D3',
            'SUPPLIER_S1',
            'QTY_S1',
            'RATE_S1',
            'SUPPLIER_S2',
            'QTY_S2',
            'RATE_S2',
            'SUPPLIER_S3',
            'QTY_S3',
            'RATE_S3'
        ]

        organization_id = os.environ.get('DISTRIBUTOR_ORG_ID', 303)
        chunk_size = 50
        stock_df =  pd.read_excel(instance.content)
        columns_from_file = stock_df.columns.to_list()
        missing_columns = list(set(purchase_prediction_columns) - set(columns_from_file))
        row, column = stock_df.shape
        index = 0
        if not missing_columns:
            while index < row:
                next_index = index + chunk_size
                create_purchase_prediction_from_file_lazy.apply_async(
                    (
                        instance.name,
                        instance.pk,
                        index,
                        next_index,
                        organization_id,
                    ),
                    countdown=5,
                    retry=True, retry_policy={
                        'max_retries': 10,
                        'interval_start': 0,
                        'interval_step': 0.2,
                        'interval_max': 0.2,
                    }
                )
                index = next_index


def post_save_delivery_hub(sender, instance, created, **kwargs):

    user_detail_cache_expires_by_organization_delivery_thana(instance.hub_areas)
    # Delete delivery area hub id cache
    cache_key = DELIVERY_AREA_HUB_ID_CACHE_KEY
    cache.delete(cache_key)


def post_save_area(sender, instance, created, **kwargs):
    from core.models import Organization

    organizations = Organization.objects.filter(
        area_id = instance.id
    ).values_list("id")
    get_or_clear_cumulative_discount_factor(organization_ids=organizations, clear=True)
    # clear related oranization and area discounts
    clear_organization_and_area_discount_cache(
        organization_ids=organizations
    )


def pre_save_password_reset(sender, instance, **kwargs):
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        old_instance = None

    if old_instance and old_instance.reset_status != ResetStatus.SUCCESS and instance.reset_status == ResetStatus.SUCCESS:
        instance.reset_date = timezone.now()
