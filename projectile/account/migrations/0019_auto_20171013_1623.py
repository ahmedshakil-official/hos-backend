# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-13 10:23
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0018_auto_20171011_1454'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transactionhead',
            name='group',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'-'), (1, b'Patient'), (2, b'Employee'), (3, b'Supplier'), (4, b'Stack Holder'), (5, b'Referrer'), (6, b'Other'), (7, b'Service Provider')], db_index=True, default=0),
        ),
    ]