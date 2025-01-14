# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-10-16 09:24
from __future__ import unicode_literals

from django.db import migrations, models
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('prescription', '0032_auto_20181010_1251'),
    ]

    operations = [
        migrations.AddField(
            model_name='prescription',
            name='diagnosis_history',
            field=models.CharField(blank=True, help_text='Previous illness history', max_length=2048, null=True, verbose_name='patient previous diagnosis'),
        ),
        migrations.AddField(
            model_name='prescriptiondiagnosis',
            name='type',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Previous'), (1, b'Current')], db_index=True, default=1, help_text='Diagnosis Type'),
        ),
    ]
