# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-28 10:00
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0081_merge_20180525_0328'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='service_consumed_print_type',
            field=enumerify.fields.SelectIntegerField(choices=[(1, b'Default'), (2, b'Service Consumed Receipt')], db_index=True, default=1, help_text='Choose service consumed print type'),
        ),
    ]
