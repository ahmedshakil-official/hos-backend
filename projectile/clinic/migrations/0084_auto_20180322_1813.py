# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-22 12:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0083_auto_20180322_1720'),
    ]

    operations = [
        migrations.AddField(
            model_name='subservicereport',
            name='standard_reference',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name='subservicereport',
            name='sub_service_report_field',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='report_value_of_field', to='clinic.SubServiceReportField'),
        ),
    ]
