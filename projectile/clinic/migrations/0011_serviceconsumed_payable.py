# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-20 06:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0010_auto_20170918_1633'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceconsumed',
            name='payable',
            field=models.BooleanField(default=True),
        ),
    ]
