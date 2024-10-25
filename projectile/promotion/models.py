from django.db import models
from django.db.models.signals import post_save
from django.core.validators import MinValueValidator
from common.models import (
    CreatedAtUpdatedAtBaseModel,
    CreatedAtUpdatedAtBaseModelWithOrganization,
)
from common.fields import TimestampImageField, TimestampVersatileImageField
from .signals import post_save_published_promotion_order, post_save_popup_message


class Promotion(CreatedAtUpdatedAtBaseModel):
    message = models.TextField()
    image = TimestampImageField(upload_to='promotion/images', blank=True, null=True)

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name_plural = "Promotions"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"Message: {}".format(self.message)


class PublishedPromotion(CreatedAtUpdatedAtBaseModelWithOrganization):
    promotion = models.ForeignKey(
        Promotion,
        models.DO_NOTHING,
        blank=False,
        null=False,
        db_index=True,
        related_name='published_promotions'
    )
    # pylint: disable=old-style-class, no-init
    class Meta:
        index_together = (
            'organization',
            'promotion',
        )
        verbose_name_plural = "Published Promotions"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"Organization: {}; Promotion: {}".format(
            self.organization_id,
            self.promotion_id
        )


class PopUpMessage(CreatedAtUpdatedAtBaseModel):
    message = models.TextField(blank=True, null=True)
    is_removable = models.BooleanField(default=False)
    image = TimestampVersatileImageField(upload_to='banner/images', blank=True, null=True)
    url = models.URLField(max_length=500, blank=True, null=True)
    # if message published for all organization then is_public is true
    is_public = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    first_published_date = models.DateTimeField(null=True, blank=True)
    last_unpublished_date = models.DateTimeField(null=True, blank=True)

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name_plural = "PopUp Messages"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"Message: {}".format(self.message)


class PublishedPopUpMessage(CreatedAtUpdatedAtBaseModelWithOrganization):
    message = models.ForeignKey(
        PopUpMessage,
        models.DO_NOTHING,
        blank=False,
        null=False,
        db_index=True,
        related_name='published_messages'
    )
    # if publish date is not now or previous then we use it as scheduling date to publish in future
    publish_date = models.DateTimeField(null=True, blank=True)
    # if expires date date provide at creation then it will be use as schedule to take down
    expires_date = models.DateTimeField(null=True, blank=True)

    # pylint: disable=old-style-class, no-init
    class Meta:
        index_together = (
            'organization',
            'message',
        )
        verbose_name_plural = "Published PopUp Messages"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"Organization: {}; Message: {}".format(
            self.organization_id,
            self.message_id
        )


class PublishedPromotionOrder(CreatedAtUpdatedAtBaseModelWithOrganization):
    date = models.DateTimeField()
    contact_no = models.CharField(
        max_length=24,
        default=None,
        blank=True,
        null=True,
        help_text='Customer contact number'
    )
    published_promotion = models.ForeignKey(
        PublishedPromotion,
        models.DO_NOTHING,
        blank=False,
        null=False,
        db_index=True,
        related_name='promotion_orders'
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    amount = models.FloatField(
        validators=[MinValueValidator(0.0)],
        default=0.0
    )
    # pylint: disable=old-style-class, no-init
    class Meta:
        index_together = (
            'organization',
            'published_promotion',
        )
        verbose_name_plural = "Published Promotion Orders"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"Organization: {}; Published Promotion: {}".format(
            self.organization_id,
            self.published_promotion_id
        )


post_save.connect(post_save_published_promotion_order, sender=PublishedPromotionOrder)
post_save.connect(post_save_popup_message, sender=PopUpMessage)
