# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-08-19 10:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0151_scriptfilestorage'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='allow_sale_rate_edit',
            field=models.BooleanField(default=True, help_text='Settings for enable/disable sales rate edit'),
        ),
    ]
