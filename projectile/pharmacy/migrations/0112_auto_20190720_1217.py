# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-07-20 12:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0111_auto_20190710_1047'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='stock',
            options={'ordering': ('-local_count', '-organizationwise_count', '-global_count', 'id')},
        ),
        migrations.RemoveIndex(
            model_name='stock',
            name='pharmacy_st_status_80ec57_idx',
        ),
        migrations.RemoveIndex(
            model_name='stock',
            name='pharmacy_st_local_c_4a7ac2_idx',
        ),
        migrations.AddField(
            model_name='stock',
            name='is_salesable',
            field=models.BooleanField(default=True),
        ),
        migrations.AddIndex(
            model_name='stock',
            index=models.Index(fields=['status', 'is_salesable', 'store_point', 'stock', 'is_service', 'organization_id', 'product_full_name'], name='pharmacy_st_status_e7a3a7_idx'),
        ),
        migrations.AddIndex(
            model_name='stock',
            index=models.Index(fields=['product_len', '-local_count', '-organizationwise_count', '-global_count', 'product_full_name', 'id'], name='pharmacy_st_product_0e02ae_idx'),
        ),
        migrations.AddIndex(
            model_name='stock',
            index=models.Index(fields=['-local_count', '-organizationwise_count', '-global_count', 'product_len', 'product_full_name', 'id'], name='pharmacy_st_local_c_34b957_idx'),
        ),
        migrations.AddIndex(
            model_name='stock',
            index=models.Index(fields=['-local_count', '-organizationwise_count', '-global_count', 'id'], name='pharmacy_st_local_c_893056_idx'),
        ),
    ]
