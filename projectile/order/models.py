from django.core.validators import MinValueValidator
from django.db import models
from django_json_field_schema_validator.validators import JSONFieldSchemaValidator

from common.json_validator_schemas import validate_product_image
from common.models import CreatedAtUpdatedAtBaseModelWithOrganization

from core.models import Person

from order.utils import get_discount_for_cart_and_order_items_v2
from pharmacy.models import Stock


# Create your models here.
class Cart(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateTimeField()
    delivery_date = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(
        Person, models.CASCADE, related_name='carts')
    is_pre_order = models.BooleanField(
        default=False,
        help_text="Defines pre order / regular order cart"
    )
    sub_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    discount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    round = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    grand_total = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)

    def __str__(self):
        return f"{self.id}: {self.date} - {self.user}"

    def has_active_carts(self):
        """
        Check if a user has an active cart with is_pre_order=True
        and another cart with is_pre_order=False

        True if both types of carts exist, False otherwise.
        """
        active_pre_order_cart = Cart.objects.filter(
            user=self.user, status=True, is_pre_order=True
        ).count() == 1

        active_regular_cart = Cart.objects.filter(
            user=self.user, status=True, is_pre_order=False
        ).count() == 1

        return active_pre_order_cart and active_regular_cart

    @property
    def discount_info(self):
        context = get_discount_for_cart_and_order_items_v2(float(self.grand_total))
        return {
            'cart_and_order_grand_total': round(self.grand_total),
            'amount_to_reach_next_discount_level': context.get('amount_to_reach_next_discount_level', 0),
            'current_discount_percentage': context.get('current_discount_percentage', 0),
            "current_discount_amount": context.get('current_discount_amount', 0),
            'next_discount_percentage': context.get('next_discount_percentage', 0),
            'next_discount_amount': context.get('next_discount_amount', 0),
        }


class CartItem(CreatedAtUpdatedAtBaseModelWithOrganization):
    cart = models.ForeignKey(
        Cart, models.CASCADE,
        related_name='cart_items',
        help_text="The cart to which this item belongs."
    )
    stock = models.ForeignKey(
        Stock,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='cart_item_stocks',
        help_text="The stock associated with this cart item."
    )
    # we have lot of endpoint which requires stock alias
    stock_alias = models.UUIDField(
        blank=True,
        null=True,
        editable=False,
        help_text="The stock alias associated with this cart item."
    )
    product_name = models.CharField(
        max_length=255,
        help_text="It contain full name of product, fullname=form+name+strength"
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    discount_rate = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    discount_amount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    total_amount = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    product_image = models.JSONField(
        blank=True,
        null=True,
        help_text="Product image data in JSON format",
        validators=[JSONFieldSchemaValidator(validate_product_image)]
    )
    mrp = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    price = models.DecimalField(default=0.00, max_digits=19, decimal_places=3)
    company_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.id}: {self.product_name} - {self.cart}"
