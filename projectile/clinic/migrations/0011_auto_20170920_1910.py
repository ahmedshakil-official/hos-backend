# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-20 13:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0010_auto_20170918_1633'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointmenttreatmentsession',
            name='bed',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='clinic.Bed'),
        ),
    ]
