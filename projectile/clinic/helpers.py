# for python3 compatibility
from __future__ import division

from django.contrib import admin

from django.db.models import Q

from common.enums import Status, PublishStatus
from core.models import PersonOrganization

from .enums import PaymentType

def get_payment_type(person_organization_id, account, amount):
    person_organization = PersonOrganization.objects.only(
        'id',
        'balance',
    ).get(
        pk=person_organization_id
    )
    if amount:
        if account:
            return PaymentType.CASH

        else:
            margin = amount + person_organization.balance
            if margin > 0 and margin >= amount:
                return PaymentType.DUE
            elif margin <= 0:
                return PaymentType.ADVANCED
            return PaymentType.PARTIAL

    return PaymentType.FREE


class SampleCollectionDateFilter(admin.SimpleListFilter):
    title = 'Sample Collection Date'

    parameter_name = 'sample_collection_date'

    def lookups(self, request, model_admin):

        return (
            ('yes', 'Not Null'),
            ('no', 'Null'),
        )

    def queryset(self, request, queryset):

        if self.value() == 'yes':
            return queryset.filter(sample_collection_date__isnull=False)

        if self.value() == 'no':
            return queryset.filter(sample_collection_date__isnull=True)


class SampleTestDateFilter(admin.SimpleListFilter):
    title = 'Sample Test Date'

    parameter_name = 'sample_test_date'

    def lookups(self, request, model_admin):

        return (
            ('yes', 'Not Null'),
            ('no', 'Null'),
        )

    def queryset(self, request, queryset):

        if self.value() == 'yes':
            return queryset.filter(sample_test_date__isnull=False)

        if self.value() == 'no':
            return queryset.filter(sample_test_date__isnull=True)


class ReportDeliveredFilter(admin.SimpleListFilter):
    title = 'Report Delivered'

    parameter_name = 'service_consumed_group__report_delivered'

    def lookups(self, request, model_admin):

        return (
            ('yes', 'Yes'),
            ('no', 'No'),
            ('null', 'null'),
        )

    def queryset(self, request, queryset):

        if self.value() == 'yes':
            return queryset.filter(service_consumed_group__report_delivered=True)

        if self.value() == 'no':
            return queryset.filter(service_consumed_group__report_delivered=False)

        if self.value() == 'null':
            return queryset.filter(service_consumed_group__report_delivered__isnull=True)


def get_service_consumeds_on_special_discount(service_consumeds, discount=0):
    """[get a list of service_consumeds in and discount]

    Keyword Arguments:
        service_consumeds {list} -- [description] (default: {[]})
        discount {int} -- [description] (default: {0})

    Returns:
        [list] -- [service_consumeds with calculated amount]
    """
    total_amount = sum(item['price'] - item['discount'] for item in service_consumeds)
    for item in service_consumeds:
        item['amount'] = float(((item['price'] - item['discount']) *\
        discount)) / float(total_amount)
    return service_consumeds


def get_service_consumeds_with_paid_amount(service_consumeds, total_paid=0):
    """[get a list of service_consumeds and total_paid of group]

    Keyword Arguments:
        service_consumeds {list} -- [description] (default: {[]})
        amount {int} -- [description] (default: {0})

    Returns:
        [list] -- [service_consumeds with calculated paid amount]
    """
    copy_service_consumeds = []
    total_amount = sum([item['price'] - item['discount'] for item in service_consumeds])
    for item in service_consumeds:
        try:
            paid = float(((item['price'] - item['discount']) * total_paid)) / float(total_amount)
        except ZeroDivisionError:
            paid = 0
        copy_service_consumeds.append({
            'id': item['id'],
            'paid': paid
        })
    return copy_service_consumeds


def update_service_consumed_paid(group):
    from .models import ServiceConsumed
    service_consumeds = get_service_consumeds_with_paid_amount(
        group.service_consumed_group.filter(
            status=Status.ACTIVE
        ).values('id', 'price', 'discount'), group.paid
    )
    for item in service_consumeds:
        ServiceConsumed.objects.filter(
            ~Q(paid=item['paid']), pk=item['id']).update(paid=item['paid'])
        # service_consumed = ServiceConsumed.objects.get(pk=item['id'])
        # if service_consumed.paid != item['paid']:
        #     service_consumed.paid = item['paid']
        #     service_consumed.save(update_fields=['paid',])



def create_or_update_products_of_service(
        self,
        sub_service,
        new_list=None,
        update_list=None,
        removed_list=None
    ):
    """[perform database operation based on lists values]
    Arguments:
        sub_service {[int]} -- [subservice id]
        new_list {[list of dict]} -- [to be newly added instances]
        update_list {[list of dict]} -- [to be updated]
        removed_list {[list of int]} -- [to be removed(update status)]
    """
    from .models import ProductOfService

    if new_list:
        for item in new_list:
            product_of_service = ProductOfService(
                sub_service_id=sub_service,
                product_id=item['product'],
                quantity=item['quantity'],
                entry_by=self.request.user,
                organization=self.request.user.organization,
            )
            product_of_service.save()

    if update_list:
        for item in update_list:
            product_of_service = ProductOfService.objects.get(pk=item['id'])
            product_of_service.quantity = item['quantity']
            product_of_service.updated_by = self.request.user
            product_of_service.save(update_fields=['quantity', 'updated_by'])

    if removed_list:
        for item in removed_list:
            product_of_service = ProductOfService.objects.get(pk=item)
            product_of_service.status = Status.INACTIVE
            product_of_service.save(update_fields=['status'])


def get_distributed_amount_based_on_head(total, transaction_amount, required):
    """[summary]
    Arguments:
        total {[float]} -- [total service amount]
        transaction_amount {[float]} -- [transaction amount]
        required {[float]} -- [headwise service amount]
    Returns:
        [float] -- [distributed amount per unique head]
    """
    try:
        percentage = float(required * 100) / total
        return float(percentage * transaction_amount) / 100
    except ZeroDivisionError:
        return 0
