# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-12-05 14:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0087_purchase_round_discount'),
    ]

    operations = [
        migrations.AddField(
            model_name='sales',
            name='editable',
            field=models.BooleanField(default=False),
        ),
    ]
