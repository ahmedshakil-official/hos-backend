
from django.contrib import admin
from common.admin import CreatedAtUpdatedAtBaseModelWithOrganizationAdmin, CreatedAtUpdatedAtBaseModel
from .models import Delivery, OrderDeliveryConnector, StockDelivery


@admin.register(Delivery)
class DeliveryAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass


@admin.register(OrderDeliveryConnector)
class OrderDeliveryConnectorAdmin(CreatedAtUpdatedAtBaseModel):
    pass


@admin.register(StockDelivery)
class StockDeliveryAdmin(CreatedAtUpdatedAtBaseModel):
    pass

