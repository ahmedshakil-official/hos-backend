# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-22 08:50
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0003_auto_20170619_0809'),
    ]

    operations = [
        migrations.AddField(
            model_name='productgroup',
            name='type',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Medicine'), (1, b'Other')], db_index=True, default=1),
        ),
    ]
