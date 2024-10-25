# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-21 12:33
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0080_merge_20180321_1120'),
    ]

    operations = [
        migrations.AddField(
            model_name='subservicereportfield',
            name='category',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='report_of_category', to='clinic.ReportFieldCategory'),
        ),
        migrations.AddField(
            model_name='subservicereportfield',
            name='category_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='subservicereportfield',
            name='investigation_field',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='report_of_investigation', to='clinic.InvestigationField'),
        ),
        migrations.AddField(
            model_name='subservicereportfield',
            name='price',
            field=models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
    ]
