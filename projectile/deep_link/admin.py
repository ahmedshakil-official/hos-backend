"""Admin panel configuration for deep link app."""

from django.contrib import admin

from common.admin import CreatedAtUpdatedAtBaseModel

from deep_link.models import DeepLink


@admin.register(DeepLink)
class DeepLinkAdmin(CreatedAtUpdatedAtBaseModel):
    pass