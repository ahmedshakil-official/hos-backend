# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-14 10:37
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0006_auto_20170714_0825'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stocktransfer',
            name='discount',
        ),
    ]
