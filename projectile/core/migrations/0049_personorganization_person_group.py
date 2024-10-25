# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-16 11:16
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0048_personorganization_opening_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='personorganization',
            name='person_group',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'Patient'), (1, b'Employee'), (2, b'Stack Holder'), (3, b'Supplier'), (4, b'Board of Director'), (5, b'System Admin'), (6, b'Referrer'), (7, b'Service Provider'), (8, b'Other')], db_index=True, default=0),
        ),
    ]