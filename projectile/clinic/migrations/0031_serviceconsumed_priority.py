# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-09 13:12
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0030_auto_20171009_1325'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceconsumed',
            name='priority',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Normal'), (1, b'Low'), (2, b'High')], db_index=True, default=0),
        ),
    ]
