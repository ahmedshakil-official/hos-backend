# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-25 11:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0055_merge_20180125_1353'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='appointment_bulk_sms',
            field=models.BooleanField(default=False),
        ),
    ]
