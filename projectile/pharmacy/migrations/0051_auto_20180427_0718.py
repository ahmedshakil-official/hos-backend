# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-27 07:18
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0050_auto_20180412_0732'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockiolog',
            name='conversion_factor',
            field=models.FloatField(default=1.0, validators=[django.core.validators.MinValueValidator(0.09)]),
        ),
        migrations.AddField(
            model_name='stockiolog',
            name='primary_unit',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='stock_io_primary_unit', to='pharmacy.Unit'),
        ),
        migrations.AddField(
            model_name='stockiolog',
            name='secondary_unit',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='stock_io_secondary_unit', to='pharmacy.Unit'),
        ),
        migrations.AddField(
            model_name='stockiolog',
            name='secondary_unit_flag',
            field=models.BooleanField(default=False),
        ),
    ]
