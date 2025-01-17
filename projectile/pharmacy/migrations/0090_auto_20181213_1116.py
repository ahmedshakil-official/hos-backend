# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-12-13 11:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0089_auto_20181213_1012'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='calculated_price_organization_wise',
            field=models.FloatField(default=0.0, help_text='Rate of individual product organization-wise after calculating vat, tax, discount'),
        ),
        migrations.AlterField(
            model_name='stock',
            name='calculated_price',
            field=models.FloatField(default=0.0, help_text='Rate of individual product stockpoint-wise after calculating vat, tax, discount'),
        ),
    ]
