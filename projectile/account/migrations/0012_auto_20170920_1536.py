# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-20 09:36
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0011_merge_20170915_2014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accounts',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='transactionhead',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed')], db_index=True, default=0),
        ),
    ]
