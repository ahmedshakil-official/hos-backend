# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-23 12:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0139_organizationsetting_report_print_header'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsetting',
            name='allow_default_discount_vat_rate',
            field=models.BooleanField(default=True, help_text='Settings for allowing default discount vat rate in io panel'),
        ),
    ]
