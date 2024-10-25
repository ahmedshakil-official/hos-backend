"""Models for our Deep Linking Application."""

from django.db import models

from common.models import NameSlugDescriptionBaseModel


class DeepLink(NameSlugDescriptionBaseModel):
    # Making url field to text field to store very long url
    long_dynamic_link = models.TextField(
        blank=True,
        null=True,
    )
    original_link = models.TextField()
    short_link = models.URLField(unique=True)

    def __str__(self):
        return f"{self.short_link}"
