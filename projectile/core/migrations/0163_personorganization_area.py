# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-09-27 11:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0162_organizationsetting_deduct_discount_from_referrer'),
    ]

    operations = [
        migrations.AddField(
            model_name='personorganization',
            name='area',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
