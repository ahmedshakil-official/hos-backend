from django.contrib import admin
from common.admin import (
    CreatedAtUpdatedAtBaseModel,
    CreatedAtUpdatedAtBaseModelWithOrganizationAdmin,
    NameSlugDescriptionBaseModelAdmin,
    NameSlugDescriptionBaseOrganizationWiseModelAdmin,
)

from .models import (
    ProductForm,
    ProductManufacturingCompany,
    ProductGeneric,
    ProductSubgroup,
    Product,
    ProductAdditionalInfo,
    ProductGroup,
    Unit,
    StorePoint,
    Stock,
    StockIOLog,
    Sales,
    Purchase,
    PurchaseReturn,
    PurchaseRequisition,
    StockTransferRequisition,
    StockTransfer,
    StockAdjustment,
    EmployeeAccountAccess,
    EmployeeStorepointAccess,
    SalesReturn,
    ProductCategory,
    StoreProductCategory,
    ProductDisbursementCause,
    StockIOLogDisbursementCause,
    OrganizationWiseDiscardedProduct,
    DistributorOrderGroup,
    OrderTracking,
    InvoiceFileStorage,
    ProductCompartment,
    ProductChangesLogs, StockReminder,
    DamageProduct,
    RecheckProduct,
    Damage,
)


class ProductChangesLogsAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = (
        'product',
        'organization',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )


admin.site.register(ProductChangesLogs, ProductChangesLogsAdmin)


class SalesReturnAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'purchase', 'sales',
    )
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + ('id',)
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'purchase', 'sales'
    )

admin.site.register(SalesReturn, SalesReturnAdmin)


class ProductFormAdmin(NameSlugDescriptionBaseOrganizationWiseModelAdmin):
    list_display = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_display
    list_filter = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_filter
    search_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.search_fields
    raw_id_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.raw_id_fields + ('clone',)

admin.site.register(ProductForm, ProductFormAdmin)


class ProductGroupAdmin(NameSlugDescriptionBaseOrganizationWiseModelAdmin):
    list_display = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_display + ('type',)
    list_filter = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_filter + ('type',)
    search_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.search_fields
    raw_id_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.raw_id_fields + ('clone',)

admin.site.register(ProductGroup, ProductGroupAdmin)


class ProductManufacturingCompanyAdmin(NameSlugDescriptionBaseOrganizationWiseModelAdmin):
    list_display = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_display
    list_filter = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_filter
    search_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.search_fields
    raw_id_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.raw_id_fields + ('clone',)

admin.site.register(ProductManufacturingCompany, ProductManufacturingCompanyAdmin)


class ProductGenericAdmin(NameSlugDescriptionBaseOrganizationWiseModelAdmin):
    list_display = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_display
    list_filter = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_filter
    search_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.search_fields
    raw_id_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.raw_id_fields + ('clone',)

admin.site.register(ProductGeneric, ProductGenericAdmin)


class ProductCategoryAdmin(NameSlugDescriptionBaseOrganizationWiseModelAdmin):
    list_display = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_display
    list_filter = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_filter
    search_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.search_fields
    raw_id_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.raw_id_fields + ('clone',)
admin.site.register(ProductCategory, ProductCategoryAdmin)


class ProductSubgroupAdmin(NameSlugDescriptionBaseOrganizationWiseModelAdmin):
    list_display = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_display + (
        'product_group',
    )
    list_filter = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_filter
    search_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.search_fields + (
        'product_group__name',
    )
    raw_id_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.raw_id_fields + (
        'clone', 'product_group'
    )
admin.site.register(ProductSubgroup, ProductSubgroupAdmin)


class ProductAdmin(NameSlugDescriptionBaseOrganizationWiseModelAdmin):
    list_display = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_display + (
        'trading_price', 'purchase_price',
        'manufacturing_company', 'form', 'subgroup',
        'generic', 'category',
    )
    list_filter = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_filter + (
        'global_category',
    )
    search_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.search_fields + (
        'manufacturing_company__name', 'form__name',
        'subgroup__name', 'generic__name', 'category__name'
    )
    raw_id_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.raw_id_fields + (
        'clone', 'manufacturing_company', 'form',
        'subgroup', 'generic', 'primary_unit',
        'secondary_unit', 'category'
    )
    readonly_fields = ('full_name',)

admin.site.register(Product, ProductAdmin)

class ProductAdditionalInfoAdmin(CreatedAtUpdatedAtBaseModel):
    list_display = CreatedAtUpdatedAtBaseModel.list_display + (
        'product', 'administration',
    )
    list_filter = CreatedAtUpdatedAtBaseModel.list_filter
    search_fields = CreatedAtUpdatedAtBaseModel.search_fields + (
        'product__id', 'product__alias', 'product__subgroup__name',
        'product__generic__name', 'product__category__name',
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModel.raw_id_fields + (
        'product',
    )

admin.site.register(ProductAdditionalInfo, ProductAdditionalInfoAdmin)


class UnitAdmin(NameSlugDescriptionBaseOrganizationWiseModelAdmin):
    list_display = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_display
    list_filter = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_filter
    search_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.search_fields
    raw_id_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.raw_id_fields + ('clone',)

admin.site.register(Unit, UnitAdmin)


class StorePointAdmin(NameSlugDescriptionBaseModelAdmin):
    list_display = NameSlugDescriptionBaseModelAdmin.list_display + (
        'phone', 'address', 'type',
        'populate_global_product', 'organization'
    )
    list_filter = NameSlugDescriptionBaseModelAdmin.list_filter + (
        'organization', 'type',
        'populate_global_product'
    )
    search_fields = NameSlugDescriptionBaseModelAdmin.search_fields + ('phone',)
    raw_id_fields = NameSlugDescriptionBaseModelAdmin.raw_id_fields + ('organization',)

admin.site.register(StorePoint, StorePointAdmin)


class StockAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        '_store_point', 'product', 'stock', 'demand',
        'tracked',
    )

    def _store_point(self, obj):
        return obj.store_point.name

    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter + (
        'tracked',
    )
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'store_point__name', 'product__name'
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'store_point', 'product'
    )

admin.site.register(Stock, StockAdmin)


class StockIOLogAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'stock', 'quantity', 'rate', 'batch', 'expire_date', 'date',
        'type', 'conversion_factor', 'secondary_unit_flag'
    )
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter + ('type',)
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'stock__store_point__name', 'stock__product__name'
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'stock', 'sales', 'purchase', 'transfer',
        'adjustment', 'patient', 'person_organization_patient',
        'primary_unit', 'secondary_unit',
    )

admin.site.register(StockIOLog, StockIOLogAdmin)


class StockAdjustmentAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'date', '_store_point', 'employee', 'patient', 'is_product_disbrustment',
        'adjustment_type',
    )

    def _store_point(self, obj):
        return obj.store_point.name

    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter + (
        'is_product_disbrustment', 'adjustment_type'
    )
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'store_point__name',
        'employee__first_name', 'employee__last_name',
        'employee__phone', 'patient__first_name',
        'patient__last_name', 'patient__phone'
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'store_point', 'employee', 'person_organization_employee', 'patient',
        'person_organization_patient', 'patient_admission', 'service_consumed',
    )

admin.site.register(StockAdjustment, StockAdjustmentAdmin)


class SalesAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'sale_date', 'buyer', 'amount', 'discount', 'paid_amount', 'salesman',
        'remarks', 'patient_admission', 'vouchar_no', 'sales_type',
        'is_purchase_return',
    )
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter + (
        'sales_type', 'is_purchase_return', 'sales_mode',
    )
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'buyer__first_name', 'buyer__last_name', 'buyer__phone',
        'salesman__first_name', 'salesman__last_name', 'salesman__phone',
        'vouchar_no',
    )
    date_hierarchy = 'sale_date'
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'store_point', 'buyer', 'person_organization_buyer', 'person_organization_salesman',
        'salesman', 'transaction', 'patient_admission', 'copied_from', 'prescription',
        'bill', 'organization_department',
    )

admin.site.register(Sales, SalesAdmin)


class StockTransferRequisitionInline(admin.TabularInline):
    model = StockTransferRequisition
    fk_name = 'stock_transfer'
    raw_id_fields = ('organization', 'entry_by', 'updated_by', 'stock_transfer', 'requisition',)


class StockTransferAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    inlines = [
        StockTransferRequisitionInline
    ]
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'date', 'transfer_from', 'transfer_to', 'transport',
        'by', 'transfer_status', 'remarks',
    )
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter + (
        'transfer_status',
    )
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'transfer_from__name', 'transfer_to__name', 'by__first_name',
        'by__last_name', 'by__phone',
    )
    date_hierarchy = 'date'
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'transfer_from', 'transfer_to', 'by', 'person_organization_by',
        'received_by', 'person_organization_received_by', 'copied_from', 'requisitions',
    )

admin.site.register(StockTransfer, StockTransferAdmin)


class PurchaseRequisitionInline(admin.TabularInline):
    model = PurchaseRequisition
    fk_name = 'purchase'
    raw_id_fields = ('organization', 'entry_by', 'updated_by', 'purchase', 'requisition',)


class SalesReturnInline(admin.TabularInline):
    model = SalesReturn
    fk_name = 'purchase'
    raw_id_fields = ('organization', 'entry_by', 'updated_by', 'purchase', 'sales',)


class PurchaseAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    inlines = [
        PurchaseRequisitionInline,
        SalesReturnInline,
    ]
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'purchase_date', 'purchase_type', 'supplier',
        '_department', 'amount', 'discount', 'vat_rate',
        'vat_total', 'tax_rate', 'tax_total', 'grand_total',
        'purchase_payment', 'receiver',
    )
    def _department(self, obj):
        if obj.department:
            return obj.department.name
        return None
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter + (
        'is_sales_return', 'purchase_type'
    )
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'supplier__first_name', 'supplier__last_name', 'supplier__phone',
        'department__name', 'receiver__first_name', 'receiver__last_name',
        'receiver__phone', 'vouchar_no',
    )
    date_hierarchy = 'purchase_date'
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'supplier', 'person_organization_supplier', 'department', 'receiver',
        'person_organization_receiver', 'copied_from', 'requisitions',
        'patient_admission', 'store_point', 'organization_department',
    )

admin.site.register(Purchase, PurchaseAdmin)


class PurchaseReturnAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'alias', 'sales', 'purchase',
    )
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'id', 'alias',
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'sales', 'purchase'
    )

admin.site.register(PurchaseReturn, PurchaseReturnAdmin)

class EmployeeAccountAccessAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'employee', 'account', 'access_status',
    )
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter + ('access_status',)
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'employee__first_name', 'employee__last_name',
        'employee__phone', 'account__name'
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'employee',
        'person_organization', 'account'
    )

admin.site.register(EmployeeAccountAccess, EmployeeAccountAccessAdmin)


class EmployeeStorepointAccessAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'employee', '_store_point',
        'access_status',
    )

    def _store_point(self, obj):
        return obj.store_point.name

    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter + \
        ('access_status',)
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'employee__first_name', 'employee__last_name',
        'employee__phone', 'store_point__name'
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'employee',
        'person_organization', 'store_point'
    )

admin.site.register(EmployeeStorepointAccess, EmployeeStorepointAccessAdmin)


class StoreProductCategoryAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'id', '_store_point', '_product_category', 'status', 'organization'
    )

    def _store_point(self, obj):
        return obj.store_point.name

    def _product_category(self, obj):
        return obj.product_category.name

    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'store_point', 'product_category'
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'store_point', 'product_category',
    )

admin.site.register(StoreProductCategory, StoreProductCategoryAdmin)

# class SalesStockIOLogAdmin(VersionAdmin):
#     list_display = (
#         'sales', 'stock_io_log',)
#
#
# admin.site.register(SalesStockIOLog, SalesStockIOLogAdmin)
#
#
# class PurchaseStockIOLogAdmin(VersionAdmin):
#     list_display = (
#         'purchase', 'stock_io_log',)
#
#
# admin.site.register(PurchaseStockIOLog, PurchaseStockIOLogAdmin)


class ProductDisbursementCauseAdmin(NameSlugDescriptionBaseOrganizationWiseModelAdmin):
    list_display = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_display
    list_filter = NameSlugDescriptionBaseOrganizationWiseModelAdmin.list_filter
    search_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.search_fields
    raw_id_fields = NameSlugDescriptionBaseOrganizationWiseModelAdmin.raw_id_fields + ('clone',)

admin.site.register(ProductDisbursementCause, ProductDisbursementCauseAdmin)


class StockIOLogDisbursementCauseAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'stock_io_log', 'disbursement_cause',
        'number_of_usage',
    )
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'disbursement_cause__name',
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'stock_io_log', 'disbursement_cause',
    )

admin.site.register(StockIOLogDisbursementCause, StockIOLogDisbursementCauseAdmin)


class OrganizationWiseDiscardedProductAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    list_display = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_display + (
        'parent', 'product', 'entry_type'
    )
    list_filter = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.list_filter
    search_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.search_fields + (
        'parent__name', 'product__name',
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModelWithOrganizationAdmin.raw_id_fields + (
        'parent', 'product',
    )

admin.site.register(OrganizationWiseDiscardedProduct, OrganizationWiseDiscardedProductAdmin)


class DistributorOrderGroupAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass

admin.site.register(DistributorOrderGroup, DistributorOrderGroupAdmin)


class OrderTrackingAdmin(CreatedAtUpdatedAtBaseModel):
    pass

admin.site.register(OrderTracking, OrderTrackingAdmin)

class InvoiceFileStorageAdmin(CreatedAtUpdatedAtBaseModel):
    list_display = CreatedAtUpdatedAtBaseModel.list_display + (
        'content', 'content_type', 'purpose',
    )
    list_filter = CreatedAtUpdatedAtBaseModel.list_filter + (
        'content_type',
    )
    search_fields = CreatedAtUpdatedAtBaseModel.search_fields + (
        'name', 'content_type', 'alias',
    )
    raw_id_fields = CreatedAtUpdatedAtBaseModel.raw_id_fields + (
        'entry_by', 'updated_by'
    )

admin.site.register(InvoiceFileStorage, InvoiceFileStorageAdmin)


class ProductCompartmentAdmin(NameSlugDescriptionBaseOrganizationWiseModelAdmin):
    pass

admin.site.register(ProductCompartment, ProductCompartmentAdmin)


class ProductRestockReminderAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass

admin.site.register(StockReminder, ProductRestockReminderAdmin)


class DamageProductAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass

admin.site.register(DamageProduct)


class RecheckProductAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass

admin.site.register(RecheckProduct)
admin.site.register(Damage)
