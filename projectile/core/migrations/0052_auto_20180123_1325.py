# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-23 07:25
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0051_organizationsetting_display_patient_is_positive'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='type',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Mother'), (1, b'Branch'), (2, b'Unite'), (3, b'Private Practitioners')], db_index=True, default=0),
        ),
    ]
