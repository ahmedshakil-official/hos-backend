# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-21 11:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0040_auto_20171219_1709'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='patient_schedule_display',
            field=models.BooleanField(default=False),
        ),
    ]
