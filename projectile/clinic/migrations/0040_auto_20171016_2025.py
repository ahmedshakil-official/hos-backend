# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-16 14:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0039_merge_20171013_1654'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointmenttreatmentsession',
            name='remarks',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
