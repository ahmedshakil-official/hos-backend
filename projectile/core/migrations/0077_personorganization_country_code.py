# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-07 10:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0076_auto_20180427_1326'),
    ]

    operations = [
        migrations.AddField(
            model_name='personorganization',
            name='country_code',
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
