# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-05 07:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0026_auto_20171002_1524'),
        ('core', '0016_auto_20171003_2023'),
    ]

    operations = [
        migrations.AddField(
            model_name='personorganization',
            name='duty_shift',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='clinic.DutyShift'),
        ),
    ]
