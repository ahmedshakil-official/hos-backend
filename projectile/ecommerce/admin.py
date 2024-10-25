
from django.contrib import admin
from common.admin import CreatedAtUpdatedAtBaseModelWithOrganizationAdmin, CreatedAtUpdatedAtBaseModel
from .models import (
    ShortReturnItem,
    ShortReturnLog,
    OrderInvoiceGroup,
    InvoiceGroupDeliverySheet,
    DeliverySheetItem,
    DeliverySheetInvoiceGroup,
    Wishlist,
    WishlistItem,
    TopSheetSubTopSheet,
    InvoiceGroupPdf,
    InvoicePdfGroup,
)

@admin.register(ShortReturnLog)
class ShortReturnLogAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


@admin.register(ShortReturnItem)
class ShortReturnItemAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


@admin.register(OrderInvoiceGroup)
class OrderInvoiceGroupAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


@admin.register(InvoiceGroupDeliverySheet)
class InvoiceGroupDeliverySheetAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


@admin.register(DeliverySheetItem)
class DeliverySheetItemAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


@admin.register(DeliverySheetInvoiceGroup)
class DeliverySheetInvoiceGroupAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass

@admin.register(TopSheetSubTopSheet)
class TopSheetSubTopSheetAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


class WishlistAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'id',
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'organization':
            kwargs['help_text'] = 'Organization responsible for adding items to the wishlist'
        return super().formfield_for_dbfield(db_field, **kwargs)


admin.site.register(Wishlist, WishlistAdmin)


class WishlistItemAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_filter = CreatedAtUpdatedAtBaseModel.list_filter
    search_fields = CreatedAtUpdatedAtBaseModel.search_fields + (
        'id',
    )


admin.site.register(WishlistItem, WishlistItemAdmin)

@admin.register(InvoiceGroupPdf)
class InvoiceGroupPdfAdmin(CreatedAtUpdatedAtBaseModel):
    pass

@admin.register(InvoicePdfGroup)
class InvoicePdfGroupAdmin(CreatedAtUpdatedAtBaseModel):
    pass
