# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-01-03 08:12
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0058_auto_20181114_1224'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='method',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'-'), (1, b'Cash'), (2, b'Cheque'), (3, b'Mobile Banking'), (4, b'Bank Draft'), (5, b'Card')], db_index=True, default=0, verbose_name=b'method of transaction'),
        ),
    ]
