import datetime

from django.db import models
from django.utils.translation import gettext as _
from django.db.models.functions import Coalesce
from django.db.models.aggregates import Sum
from django.db.models import F
from django.db.models.signals import post_save

from enumerify import fields

from common.models import CreatedAtUpdatedAtBaseModelWithOrganization, CreatedAtUpdatedAtBaseModel

from .enums import DeliveryTrackingStatus
from .signals import post_save_order_delivery, post_save_delivery


class Delivery(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateTimeField(auto_now=True)
    assigned_by = models.ForeignKey(
        'core.PersonOrganization', models.DO_NOTHING,
        verbose_name=('Assigned to a delivery man'),
        related_name='delivery_assigned_by'
    )
    assigned_to = models.ForeignKey(
        'core.PersonOrganization', models.DO_NOTHING,
        verbose_name=('Person responsible for a delivery'),
        related_name='delivery_assigned_to'
    )
    order_by_organization = models.ForeignKey(
        'core.Organization', models.DO_NOTHING,
        related_name='organization_order_by'
    )
    priority = models.PositiveIntegerField(default=1)
    # subtotal amount : sum of all orders amount
    amount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    # discount : sum of all orders discount without round amount
    discount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    # discount_rate: to trace is discount given by rate or amount
    discount_rate = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    # discount round : another form of discount
    round_discount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    vat_rate = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    # total vat for all orders
    vat_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    tax_rate = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    # total tax for all orders
    tax_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    # Net amount after calculating discount, round_discount, vat, text etc.
    grand_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    # total delivery charge for all orders
    delivery_charge = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    tracking_status = fields.SelectIntegerField(
        blueprint=DeliveryTrackingStatus,
        default=DeliveryTrackingStatus.READY_TO_DELIVER
    )
    orders = models.ManyToManyField(
        'pharmacy.Purchase', through='delivery.OrderDeliveryConnector',
        related_name='delivery_orders'
    )


    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.assigned_by, self.assigned_to)

    def update_amount_related_data(self):
        orders = self.orders.filter()
        if orders.exists():
            total_data = orders.values('organization').aggregate(
                total_amount=Coalesce(Sum(F('amount')), 0.00),
                total_discount=Coalesce(Sum(F('discount')), 0.00),
                total_round_discount=Coalesce(Sum(F('round_discount')), 0.00),
                total_grand_total=Coalesce(Sum(F('grand_total')), 0.00),
            )
            data = {key.replace('total_', ''): value for key, value in total_data.items()}
            self.__dict__.update(**data)
            self.save(update_fields=list(data.keys()))


class OrderDeliveryConnector(CreatedAtUpdatedAtBaseModel):
    order = models.ForeignKey(
        'pharmacy.Purchase', models.DO_NOTHING,
    )
    delivery = models.ForeignKey(
        Delivery, models.DO_NOTHING,
    )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.order, self.delivery)


class StockDelivery(CreatedAtUpdatedAtBaseModelWithOrganization):
    stock = models.ForeignKey(
        'pharmacy.Stock',
        models.DO_NOTHING,
        related_name='stocks_delivery'
    )
    stock_io = models.ForeignKey(
        'pharmacy.StockIOLog',
        models.DO_NOTHING,
        related_name='stock_io_delivery'
    )
    order = models.ForeignKey(
        'pharmacy.Purchase',
        models.DO_NOTHING,
        related_name='products'
    )
    delivery = models.ForeignKey(
        Delivery, models.DO_NOTHING,
    )
    product_name = models.CharField(max_length=512)
    quantity = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    rate = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    batch = models.CharField(max_length=128)
    expire_date = models.DateField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    discount_rate = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    discount_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    vat_rate = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    vat_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    tax_rate = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    tax_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    unit = models.CharField(max_length=56)
    round_discount = models.DecimalField(
        default=0.00,
        max_digits=19,
        decimal_places=3,
        help_text="discount amount distributed by inventory's round_discount"
    )
    tracking_status = fields.SelectIntegerField(
        blueprint=DeliveryTrackingStatus,
        default=DeliveryTrackingStatus.PENDING
    )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(self.id, self.created_at, self.stock)


post_save.connect(post_save_order_delivery, sender=OrderDeliveryConnector)
post_save.connect(post_save_delivery, sender=Delivery)

