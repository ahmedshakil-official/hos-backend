
from django.contrib import admin

from simple_history.admin import SimpleHistoryAdmin

from common.admin import CreatedAtUpdatedAtBaseModelWithOrganizationAdmin, CreatedAtUpdatedAtBaseModel
from .models import (
    PurchasePrediction,
    PredictionItem,
    PredictionItemSupplier,
    Procure,
    ProcureItem,
    ProcureIssueLog,
    PredictionItemMark,
    ProcureStatus, ProcureGroup,
    ProcureReturn,
    ReturnSettlement,
    ProcurePayment,
)

@admin.register(PurchasePrediction)
class PurchasePredictionAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


@admin.register(PredictionItem)
class PredictionItemAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


@admin.register(PredictionItemSupplier)
class PredictionItemSupplierAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


@admin.register(Procure)
class ProcureAdmin(SimpleHistoryAdmin, CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


@admin.register(ProcureItem)
class ProcureItemAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


@admin.register(ProcureIssueLog)
class ProcureIssueLogAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


@admin.register(PredictionItemMark)
class PredictionItemMarkAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


@admin.register(ProcureStatus)
class ProcureStatusAdmin(CreatedAtUpdatedAtBaseModel):
    pass


@admin.register(ProcureGroup)
class ProcureGroupAdmin(SimpleHistoryAdmin, CreatedAtUpdatedAtBaseModel):
    pass


@admin.register(ProcureReturn)
class ProcureReturnAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


@admin.register(ReturnSettlement)
class ReturnSettlementAdmin(CreatedAtUpdatedAtBaseModel):
    pass


@admin.register(ProcurePayment)
class ProcurePaymentAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass
