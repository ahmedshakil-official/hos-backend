# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-13 10:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0043_auto_20180307_1856'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_service',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='stock',
            name='is_service',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='product',
            name='manufacturing_company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='pharmacy.ProductManufacturingCompany'),
        ),
        migrations.AlterField(
            model_name='product',
            name='subgroup',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='pharmacy.ProductSubgroup'),
        ),
    ]
