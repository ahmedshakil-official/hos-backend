# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-06 09:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0004_productgroup_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockiolog',
            name='date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
