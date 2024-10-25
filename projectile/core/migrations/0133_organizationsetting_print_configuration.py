# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-03-15 12:46
from __future__ import unicode_literals

from django.db import migrations
import enumerify.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0132_organizationsetting_salary_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='print_configuration',
            field=enumerify.fields.SelectIntegerField(choices=[(0, b'-'), (1, b'Sweet Alert Off'), (2, b'Sweet Alert On')], db_index=True, default=2),
        ),
    ]
