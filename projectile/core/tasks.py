from __future__ import absolute_import

import logging, os

from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.hashers import make_password, check_password

from projectile.celery import app

logger = logging.getLogger(__name__)
# from celery import shared_task
from common.enums import Status
from core.models import Organization
from core.enums import LoginFailureReason, PersonGroupType


# @shared_task
def send_email(context, template, to_email, subject):
    html_body = render_to_string(template, context)
    msg = EmailMultiAlternatives(subject=subject, to=[to_email])
    msg.attach_alternative(html_body, "text/html")
    msg.send()
    logger.info(u"Email sent to: {}, Subject: {}".format(to_email, subject))
    logger.info(u"Email was sent with contex : {}, template : {}, to : {}, subject {} ".format(
        context, template, to_email, subject))

@app.task
def create_failure_log(user_name, password, message):
    from core.models import AuthLog, Person
    phone = user_name
    failure_reason = LoginFailureReason.OTHERS
    entry_by = None
    try:
        user = Person.objects.only('password').get(
            status=Status.ACTIVE,
            person_group=PersonGroupType.EMPLOYEE,
            phone=phone
        )
        is_valid_password = check_password(
            password,
            user.password
        )
        if not is_valid_password:
            failure_reason = LoginFailureReason.WRONG_PASSWORD
        entry_by = user
    except Person.DoesNotExist:
        failure_reason = LoginFailureReason.INVALID_USER
    except Person.MultipleObjectsReturned:
        failure_reason = LoginFailureReason.OTHERS

    auth_log = AuthLog.objects.create(
        entry_by=entry_by,
        failure_reason=failure_reason,
        phone=phone,
        password=make_password(password),
        error_message=message
    )
    auth_log.save()

@app.task(autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=5, max_retries=10)
def update_organization_responsible_employee_from_invoice_groups_on_bg(invoice_groups, responsible_employee_id):
    from core.helpers import update_organization_responsible_employee
    from ecommerce.models import OrderInvoiceGroup

    organization_id_list = OrderInvoiceGroup.objects.filter(
        pk__in=invoice_groups
    ).values_list('order_by_organization', flat=True)

    for organization_id in list(organization_id_list):
        update_organization_responsible_employee(
            organization_id,
            responsible_employee_id
        )

@app.task(autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=5, max_retries=10)
def update_organization_responsible_employee_from_organization_list(organization_id_list):
    from ecommerce.models import OrderInvoiceGroup

    from pharmacy.enums import OrderTrackingStatus
    from core.helpers import update_organization_responsible_employee_from_invoices

    invoice_groups = OrderInvoiceGroup.objects.filter(
        order_by_organization__pk__in=organization_id_list
    ).select_related('order_by_organization').values(
        'delivery_date',
        'responsible_employee',
        'order_by_organization'
    ).exclude(
        current_order_status__in=[
            OrderTrackingStatus.REJECTED,
            OrderTrackingStatus.CANCELLED
        ]
    ).order_by('-delivery_date').distinct('delivery_date', 'order_by_organization')

    organization_ids = update_organization_responsible_employee_from_invoices(invoice_groups)
    logger.info(
        f"Organization responsible employee updated successfully for organization IDs: {organization_ids}"
    )
