# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-10 13:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0138_serviceconsumedgroup_sub_services'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serviceconsumedgroup',
            name='sub_services',
            field=models.TextField(blank=True, max_length=2048, null=True),
        ),
    ]
