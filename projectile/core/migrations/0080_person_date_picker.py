# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-16 05:40
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0079_personorganizationdiscount_bill'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='date_picker',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'-'), (1, b'Default Date Picker'), (2, b'Give In Year')], db_index=True, default=1),
        ),
    ]
