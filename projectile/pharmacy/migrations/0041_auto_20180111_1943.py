# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-11 13:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0040_sales_storepoint'),
    ]

    operations = [
        migrations.RenameField(
            model_name='purchase',
            old_name='storepoint',
            new_name='store_point',
        ),
        migrations.RenameField(
            model_name='sales',
            old_name='storepoint',
            new_name='store_point',
        ),
    ]
