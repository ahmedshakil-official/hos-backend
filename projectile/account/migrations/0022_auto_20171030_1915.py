# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-30 13:15
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0021_auto_20171020_1139'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accounts',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='transactionhead',
            name='status',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Active'), (1, b'Inactive'), (2, b'Draft'), (3, b'Completed'), (4, b'Approved Draft')], db_index=True, default=0),
        ),
    ]
