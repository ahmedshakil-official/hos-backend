# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-27 10:41
from __future__ import unicode_literals

import common.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0051_auto_20180427_0718'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='conversion_factor',
            field=models.FloatField(default=1.0, validators=[common.validators.positive_non_zero]),
        ),
        migrations.AlterField(
            model_name='stockiolog',
            name='conversion_factor',
            field=models.FloatField(default=1.0, validators=[common.validators.positive_non_zero]),
        ),
    ]
