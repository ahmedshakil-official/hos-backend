# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-13 07:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0008_auto_20170802_1310'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='is_sales_return',
            field=models.BooleanField(default=False),
        ),
    ]
