# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-04-16 05:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0138_auto_20190405_1041'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='report_print_header',
            field=models.BooleanField(default=True, help_text='Settings for enable/disable report print header'),
        ),
    ]
