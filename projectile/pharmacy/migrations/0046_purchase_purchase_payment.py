# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-19 07:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0045_merge_20180316_1254'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='purchase_payment',
            field=models.FloatField(default=0.0),
        ),
    ]
