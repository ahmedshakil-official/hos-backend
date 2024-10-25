# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-03-18 05:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0099_sales_round_discount'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockiolog',
            name='round_discount',
            field=models.FloatField(default=0.0, help_text="discount amount distributed by inventory's round_discount"),
        ),
    ]