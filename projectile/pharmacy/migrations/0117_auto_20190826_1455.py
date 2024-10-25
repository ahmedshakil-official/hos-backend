# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-08-26 08:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0116_stockiolog_data_entry_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchase',
            name='purchase_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sales',
            name='sale_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]