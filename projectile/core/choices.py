from django.db import models


class ResetStatus(models.TextChoices):
    FAILED = "FAILED", "Failed"
    SUCCESS = "SUCCESS", "Success"
    PENDING = "PENDING", "Pending"


class ResetType(models.TextChoices):
    SELF = "SELF", "Self"
    MANUAL = "MANUAL", "Manual"


class OtpType(models.TextChoices):
    PASSWORD_RESET = "PASSWORD_RESET", "Password Reset"
    PHONE_NUMBER_RESET = "PHONE_NUMBER_RESET", "Phone Number Reset"
    OTHER = "OTHER", "Other"
