# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-09-27 06:17
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0143_auto_20190918_1455'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='discount',
            field=models.FloatField(default=0.0, help_text='discount in percentage(%)', validators=[django.core.validators.MaxValueValidator(100), django.core.validators.MinValueValidator(0)]),
        ),
    ]
