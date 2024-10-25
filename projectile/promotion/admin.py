
from reversion.admin import VersionAdmin
from django.contrib import admin

from common.admin import (
    CreatedAtUpdatedAtBaseModel,
    CreatedAtUpdatedAtBaseModelWithOrganizationAdmin,
)

from .models import (
    Promotion,
    PublishedPromotion,
    PopUpMessage,
    PublishedPopUpMessage,
    PublishedPromotionOrder,
)

class PromotionAdmin(CreatedAtUpdatedAtBaseModel):
    pass

admin.site.register(Promotion, PromotionAdmin)


class PublishedPromotionAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass

admin.site.register(PublishedPromotion, PublishedPromotionAdmin)


class PopUpMessageAdmin(CreatedAtUpdatedAtBaseModel):
    pass

admin.site.register(PopUpMessage, PopUpMessageAdmin)


class PublishedPopupMessageAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass

admin.site.register(PublishedPopUpMessage, PublishedPopupMessageAdmin)


class PublishedPromotionOrderAdmin(CreatedAtUpdatedAtBaseModelWithOrganizationAdmin):
    pass

admin.site.register(PublishedPromotionOrder, PublishedPromotionOrderAdmin)
