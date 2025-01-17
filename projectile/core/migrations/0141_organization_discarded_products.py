# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-02 11:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0103_auto_20190502_1110'),
        ('core', '0140_organizationsetting_allow_default_discount_vat_rate'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='discarded_products',
            field=models.ManyToManyField(related_name='organization_of_discarded_product', through='pharmacy.OrganizationWiseDiscardedProduct', to='pharmacy.Product'),
        ),
    ]
