# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-09-28 07:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0071_merge_20180925_1530'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='auto_adjustment',
            field=models.BooleanField(default=True),
        ),
    ]