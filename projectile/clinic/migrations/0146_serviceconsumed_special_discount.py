# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-10-14 07:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0145_serviceconsumed_referrer_deduction'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceconsumed',
            name='special_discount',
            field=models.FloatField(default=0.0, help_text='total person discount'),
        ),
    ]