# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-09 14:25
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0032_auto_20180109_1505'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='transaction',
            options={'verbose_name_plural': 'Transactions'},
        ),
    ]
