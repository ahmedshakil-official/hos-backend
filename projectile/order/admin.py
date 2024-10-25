from django.contrib import admin

from common.admin import CreatedAtUpdatedAtBaseModelWithOrganizationAdmin
from order.models import Cart, CartItem


# Register your models here.
class CartAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


admin.site.register(Cart, CartAdmin)


class CartItemAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


admin.site.register(CartItem, CartItemAdmin)

