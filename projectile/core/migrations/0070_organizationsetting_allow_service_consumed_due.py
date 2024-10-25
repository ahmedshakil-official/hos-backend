# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-06 09:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0069_merge_20180329_0744'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='allow_service_consumed_due',
            field=models.BooleanField(default=True, help_text='Settings for allow due in service consumed of this organization'),
        ),
    ]