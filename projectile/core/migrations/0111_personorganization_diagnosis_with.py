# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-10-10 05:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0110_merge_20181001_1830'),
    ]

    operations = [
        migrations.AddField(
            model_name='personorganization',
            name='diagnosis_with',
            field=models.CharField(blank=True, max_length=2048, null=True, verbose_name=b'patient diagnosis with'),
        ),
    ]
