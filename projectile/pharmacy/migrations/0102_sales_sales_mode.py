# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-04-10 10:15
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0101_auto_20190328_1822'),
    ]

    operations = [
        migrations.AddField(
            model_name='sales',
            name='sales_mode',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'-'), (1, b'Online'), (2, b'Offline'), (3, b'Other')], db_index=True, default=1, help_text='Sales is Online or Offline'),
        ),
    ]