# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-15 07:34
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0079_personorganizationdiscount_bill'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='product_vat_tax_status',
            field=enumerify.fields.SelectIntegerField(choices=[(1, b'Default'), (2, b'Product Wise')], db_index=True, default=1, help_text='Choices for product show individual vat, tax and discount or not'),
        ),
    ]
