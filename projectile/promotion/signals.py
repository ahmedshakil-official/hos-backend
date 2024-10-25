import datetime
import os

from django.db import models
from versatileimagefield.image_warmer import VersatileImageFieldWarmer
from common.tasks import send_same_sms_to_multiple_receivers, send_sms
from common.helpers import generate_phone_no_for_sending_sms

def send_order_promotion_sms_to_support(instance):
    order_by = ""
    phone_numbers = os.environ.get('NUMBERS_FOR_RECEIVING_ORDER_MESSAGE', '')
    if not phone_numbers:
        return
    phone_numbers = phone_numbers.split(',') if phone_numbers else []
    if instance.entry_by:
        try:
            order_by = instance.entry_by.get_person_organization_for_employee(
                organization=instance.organization
            ).full_name

        except:
            order_by = ""

    sms_text = "New order #{} received at {} from {}, Promotion #{}, Quantity: {}, Order by: {}, Contact no: {}".format(
        instance.id,
        instance.date.strftime('%d-%m-%Y %I:%M %p'),
        instance.organization.name,
        instance.published_promotion.promotion.id,
        instance.quantity,
        order_by,
        instance.contact_no if instance.contact_no else '#'
    )
    customer_sms_text = "Hi {}, \nThank you for your order #{}.Keep using OMIS and get exciting offers.".format(
        order_by,
        instance.id
    )
    # Send sms to support
    send_same_sms_to_multiple_receivers(phone_numbers, sms_text)
    # Send sms to customer
    sms_to = generate_phone_no_for_sending_sms(instance.contact_no)
    send_sms.delay(sms_to, customer_sms_text, instance.organization.id)

def post_save_published_promotion_order(sender, instance, created, **kwargs):
    if created:
        send_order_promotion_sms_to_support(instance)


def post_save_popup_message(sender, instance, created, **kwargs):
    if instance.image:
        product_img_warmer = VersatileImageFieldWarmer(
            instance_or_queryset=instance,
            rendition_key_set='banner_images',
            image_attr='image',
        )
        num_created, failed_to_create = product_img_warmer.warm()

