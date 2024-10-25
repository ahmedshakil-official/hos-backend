# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-01-11 12:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0091_purchase_discount_rate'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='stock',
            options={},
        ),
        migrations.AlterIndexTogether(
            name='stock',
            index_together=set([]),
        ),
        migrations.AddIndex(
            model_name='stock',
            index=models.Index(fields=['product'], name='pharmacy_st_product_1cf478_idx'),
        ),
        migrations.AddIndex(
            model_name='stock',
            index=models.Index(fields=['-local_count', '-organizationwise_count', '-global_count'], name='pharmacy_st_local_c_5e8b80_idx'),
        ),
    ]
