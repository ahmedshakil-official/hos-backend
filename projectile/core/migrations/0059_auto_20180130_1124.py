# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-30 05:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0058_auto_20180129_2042'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smslog',
            name='phone_number',
            field=models.CharField(max_length=50),
        ),
    ]
