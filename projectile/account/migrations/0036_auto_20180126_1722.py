# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-26 11:22
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0035_auto_20180126_1559'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='payabletoperson',
            options={'verbose_name': 'Payable To Person', 'verbose_name_plural': 'Payable To Persons'},
        ),
    ]