# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-06 11:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0059_auto_20180130_1124'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='trace_test_state',
            field=models.BooleanField(default=False, help_text='Settings for trace prescription test state', verbose_name='test_state'),
        ),
        migrations.AddField(
            model_name='organizationsetting',
            name='trace_test_taken_time',
            field=models.BooleanField(default=False, help_text='Settings for trace prescription test taken time', verbose_name='test_taken_time'),
        ),
    ]