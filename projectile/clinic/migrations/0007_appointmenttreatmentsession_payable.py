# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-13 06:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0006_auto_20170816_1412'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointmenttreatmentsession',
            name='payable',
            field=models.BooleanField(default=True),
        ),
    ]
