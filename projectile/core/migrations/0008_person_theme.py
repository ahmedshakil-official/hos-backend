# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-07 12:59
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20170802_1310'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='theme',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Light'), (1, b'Dark')], db_index=True, default=0),
        ),
    ]
