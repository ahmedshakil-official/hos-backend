# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-07 09:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_merge_20171101_1914'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='is_positive',
            field=models.BooleanField(default=False),
        ),
    ]