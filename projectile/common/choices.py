from django.db import models


class WriteChoices(models.TextChoices):
    POST = 'POST', 'POST'
    DELETE = 'DELETE', 'DELETE'
