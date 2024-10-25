# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-23 09:45
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0029_auto_20171117_1141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accounts',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='transactionhead',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Released'), (4, b'Approved Draft'), (5, b'Absent'), (6, b'Purchase Order')], db_index=True, default=0),
        ),
    ]