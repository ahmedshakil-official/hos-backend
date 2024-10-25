# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-07-08 08:27
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0147_auto_20190625_1826'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='data_entry_mode',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'-'), (1, b'ON'), (2, b'OFF'), (3, b'DONE')], db_index=True, default=2),
        ),
    ]
