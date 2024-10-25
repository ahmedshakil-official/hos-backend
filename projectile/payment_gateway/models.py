# from django.db import models
# from django.contrib.postgres.fields import JSONField
# from django.db.models.signals import post_save
# from enumerify import fields

# from common.models import CreatedAtUpdatedAtBaseModel
# from account.enums import OmisServices

# from .enums import Months
# from .signals import post_save_payment_response


# class PaymentRequest(CreatedAtUpdatedAtBaseModel):
#     # Initialization payload sending for generate session
#     data = JSONField()
#     # Response of the initialization request
#     response = JSONField()
#     organization = models.ForeignKey(
#         'core.Organization',
#         models.DO_NOTHING,
#         blank=True,
#         null=True,
#         db_index=True,
#         verbose_name=('organization name')
#     )
#     payment_purpose = fields.SelectIntegerField(
#         blueprint=OmisServices,
#         default=OmisServices.MONTHLY_SERVICE_CHARGE
#     )
#     payment_month = fields.SelectIntegerField(
#         blueprint=Months,
#         default=Months.JANUARY
#     )
#     discount_amount = models.FloatField(default=0.0)
#     date = models.DateTimeField(blank=True, null=True)


#     def __str__(self):
#         return self.get_name()

#     def get_name(self):
#         return u"#{}: {}".format(self.id, self.created_at)


# class PaymentIpn(CreatedAtUpdatedAtBaseModel):
#     data = JSONField()
#     payment_request = models.ForeignKey(
#         PaymentRequest,
#         models.DO_NOTHING,
#         blank=True,
#         null=True,
#         db_index=True,
#     )


#     def __str__(self):
#         return self.get_name()

#     def get_name(self):
#         return u"#{}: {}".format(self.id, self.created_at)


# class PaymentResponse(CreatedAtUpdatedAtBaseModel):
#     data = JSONField()
#     ipn = models.ForeignKey(
#         PaymentIpn,
#         models.DO_NOTHING,
#         blank=True,
#         null=True,
#         db_index=True,
#     )


#     def __str__(self):
#         return self.get_name()

#     def get_name(self):
#         return u"#{}: {}".format(self.id, self.created_at)

# post_save.connect(post_save_payment_response, sender=PaymentResponse)
