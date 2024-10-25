# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-23 07:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0106_merge_20180622_1217'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceconsumed',
            name='report_delivered',
            field=models.NullBooleanField(default=False),
        ),
        migrations.AddField(
            model_name='serviceconsumed',
            name='tentative_delivery_date',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]