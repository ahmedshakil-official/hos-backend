# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-27 06:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0042_merge_20180307_1914'),
    ]

    operations = [
        migrations.AddField(
            model_name='transactionpurchase',
            name='amount',
            field=models.FloatField(default=0),
        ),
    ]
